from datetime import date, datetime

from services.scraper_cache import ScraperCache
from services.google_calendar_api import (
    GoogleCalendarApiService,
)
from services.google_calendar_scraper import (
    GoogleCalendarScraperService,
)
from services.google_tasks import (
    GoogleTasksService,
)


def month_start(value: date) -> date:
    return date(
        value.year,
        value.month,
        1,
    )


def add_months(
    value: date,
    months: int,
) -> date:
    month_index = (
        value.year * 12
        + value.month
        - 1
        + months
    )

    year, month_zero = divmod(
        month_index,
        12,
    )

    return date(
        year,
        month_zero + 1,
        1,
    )


class CombinedCalendarService:
    """Aggregates everything the widget needs."""

    MONTHS_BACK = 1
    MONTHS_FORWARD = 2

    def __init__(self):
        self.tasks_service = (
            GoogleTasksService()
        )

        self.scraper_service = (
            GoogleCalendarScraperService()
        )

        self.scraper_cache = (
            ScraperCache()
        )

        self.calendar_api = (
            GoogleCalendarApiService()
        )

        self.scraper_status = "unknown"
        self.scraper_error = None

    def get_events(
        self,
        days_ahead=None,
    ):
        today = datetime.now().date()

        current_month = month_start(
            today
        )

        start_date = add_months(
            current_month,
            -self.MONTHS_BACK,
        )

        end_date = add_months(
            current_month,
            self.MONTHS_FORWARD + 1,
        )

        return self.get_events_between(
            start_date,
            end_date,
        )

    def get_events_between(
        self,
        start_date: date,
        end_date: date,
    ):
        # ============================================================
        # GOOGLE CALENDAR API
        # ============================================================

        events = (
            self.calendar_api
            .get_events_between(
                start_date,
                end_date,
            )
        )

        # ============================================================
        # GOOGLE TASKS API
        # ============================================================

        try:
            api_tasks = (
                self.tasks_service
                .get_tasks_between(
                    start_date,
                    end_date,
                )
            )

        except Exception as exc:
            print(
                "Google Tasks API error:",
                repr(exc),
            )

            api_tasks = []

        # ============================================================
        # GOOGLE CALENDAR SCRAPER
        # ============================================================

        try:
            scraped_tasks = (
                self._get_scraper_tasks_safely(
                    start_date,
                    end_date,
                )
            )

        except Exception as exc:
            self.scraper_status = "cached"
            self.scraper_error = str(exc)

            print(
                "Task scraper error:",
                repr(exc),
            )

            scraped_tasks = (
                self._get_cached_tasks_between(
                    start_date,
                    end_date,
                )
            )

            print(
                "Using last-known-good "
                "scraper cache:",
                len(scraped_tasks),
                "tasks",
            )

        # ============================================================
        # MERGE SOURCES
        # ============================================================

        items = {}

        for event in events:
            items[
                self._item_key(event)
            ] = event

        # Tasks API first.
        for task in api_tasks:
            items[
                self._item_key(task)
            ] = task

        # Scraper/cache last because it may
        # contain recurring occurrences and
        # richer Calendar UI information.
        for task in scraped_tasks:
            items[
                self._item_key(task)
            ] = task

        result = list(
            items.values()
        )

        result.sort(
            key=lambda item: (
                item.sort_key()
            )
        )

        return result

    # ================================================================
    # SCRAPER RELIABILITY
    # ================================================================

    def _get_scraper_tasks_safely(
        self,
        start_date: date,
        end_date: date,
    ):
        cached_tasks = (
            self._get_cached_tasks_between(
                start_date,
                end_date,
            )
        )

        # First normal scrape.
        scraped_tasks = (
            self.scraper_service
            .get_tasks_between(
                start_date,
                end_date,
            )
        )

        # ------------------------------------------------------------
        # Normal case: scraper found tasks.
        # ------------------------------------------------------------

        if scraped_tasks:
            self._accept_scraper_result(
                scraped_tasks
            )

            return scraped_tasks

        # ------------------------------------------------------------
        # Empty result is perfectly valid if the
        # previous cache for the same range was
        # also empty.
        # ------------------------------------------------------------

        if not cached_tasks:
            self._accept_scraper_result(
                scraped_tasks
            )

            return scraped_tasks

        # ------------------------------------------------------------
        # Suspicious case:
        #
        # Previous known-good scraper data had
        # tasks, but fresh scrape suddenly found
        # absolutely nothing.
        #
        # Do not trust it immediately.
        # ------------------------------------------------------------

        print(
            "SCRAPER ANOMALY: fresh result "
            "contains 0 tasks but cache has",
            len(cached_tasks),
            "tasks. Retrying...",
        )

        # Second independent scrape.
        retry_tasks = (
            self.scraper_service
            .get_tasks_between(
                start_date,
                end_date,
            )
        )

        # If retry finds something, the first
        # zero was probably a transient render
        # problem.
        if retry_tasks:
            print(
                "SCRAPER ANOMALY RECOVERED:",
                len(retry_tasks),
                "tasks found on retry.",
            )

            self._accept_scraper_result(
                retry_tasks
            )

            return retry_tasks

        # Both attempts returned zero while
        # known-good cache contains data.
        #
        # We cannot prove whether the user really
        # deleted every task or Google changed the
        # UI, so protect known-good data and warn.
        reason = (
            "Scraper returned 0 tasks twice, "
            "but last-known-good cache contains "
            f"{len(cached_tasks)} tasks. "
            "Fresh empty data was not trusted."
        )

        try:
            self.scraper_service.save_diagnostics_between(
                start_date,
                end_date,
                reason,
            )
        except Exception as diagnostic_exc:
            print(
                "Could not save anomaly diagnostic:",
                repr(diagnostic_exc),
            )

        raise RuntimeError(reason)

    def _accept_scraper_result(
        self,
        scraped_tasks,
    ) -> None:
        self.scraper_cache.save(
            scraped_tasks
        )

        self.scraper_status = (
            "healthy"
        )

        self.scraper_error = None

        print(
            "Scraper successful. "
            "Cache updated:",
            len(scraped_tasks),
            "tasks",
        )

    def _get_cached_tasks_between(
        self,
        start_date: date,
        end_date: date,
    ):
        cached_tasks = (
            self.scraper_cache.load()
        )

        return self._filter_tasks_between(
            cached_tasks,
            start_date,
            end_date,
        )

    # ================================================================
    # FILTERING
    # ================================================================

    def _filter_tasks_between(
        self,
        tasks,
        start_date: date,
        end_date: date,
    ):
        return [
            task
            for task in tasks
            if (
                start_date
                <= task.event_date
                < end_date
            )
        ]

    # ================================================================
    # MERGE KEYS
    # ================================================================

    def _item_key(
        self,
        item,
    ):
        if item.item_type == "task":
            return (
                "task",
                item.summary
                .strip()
                .lower(),
                item.event_date,
            )

        if item.event_id:
            return (
                "event-id",
                item.event_id,
                item.event_date,
            )

        start_time = (
            item.start.strftime(
                "%H:%M"
            )
            if isinstance(
                item.start,
                datetime,
            )
            else "ALL_DAY"
        )

        end_time = (
            item.end.strftime(
                "%H:%M"
            )
            if isinstance(
                item.end,
                datetime,
            )
            else ""
        )

        return (
            "event",
            item.summary
            .strip()
            .lower(),
            item.event_date,
            start_time,
            end_time,
        )

    # ================================================================
    # STATUS
    # ================================================================

    def get_scraper_status(
        self,
    ):
        return {
            "status":
                self.scraper_status,
            "error":
                self.scraper_error,
        }

    # ================================================================
    # CREATE EVENT
    # ================================================================

    def create_event(
        self,
        event,
    ):
        if event.item_type == "task":
            return (
                self.tasks_service
                .create_task(event)
            )

        return (
            self.calendar_api
            .create_event(event)
        )