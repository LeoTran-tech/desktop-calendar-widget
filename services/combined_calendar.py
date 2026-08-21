from datetime import date, datetime

from services.google_calendar_api import GoogleCalendarApiService
from services.google_calendar_scraper import GoogleCalendarScraperService
from services.google_tasks import GoogleTasksService


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
    """Aggregates everything the widget needs for its visible date range."""

    MONTHS_BACK = 1
    MONTHS_FORWARD = 2

    def __init__(self):
        self.tasks_service = (
            GoogleTasksService()
        )
        self.scraper_service = (
            GoogleCalendarScraperService()
        )
        self.calendar_api = (
            GoogleCalendarApiService()
        )

    def get_events(
        self,
        days_ahead=None,
    ):
        # The right panel still decides whether it shows 7/14/30 days.
        # The service loads the four months needed by the left calendar:
        # previous month + current month + next two months.
        today = datetime.now().date()
        current_month = month_start(today)

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
        events = (
            self.calendar_api
            .get_events_between(
                start_date,
                end_date,
            )
)

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
                exc,
            )
            api_tasks = []

        try:
            scraped_tasks = (
                self.scraper_service
                .get_tasks_between(
                    start_date,
                    end_date,
                )
            )

            for task in scraped_tasks:
                print(
                    "SCRAPED:",
                    task.summary,
                    task.start,
                )

        except Exception as exc:
            print(
                "Task scraper error:",
                repr(exc),
            )
            scraped_tasks = []

        items = {}

        for event in events:
            items[
                self._item_key(event)
            ] = event

        # API task first: this gives us coverage, including previous-month
        # completed tasks. The scraper then replaces matching task/date pairs
        # when it has richer time information from Calendar's UI.
        for task in api_tasks:
            items[
                self._item_key(task)
            ] = task

        for task in scraped_tasks:
            items[
                self._item_key(task)
            ] = task

        result = list(
            items.values()
        )
        result.sort(
            key=lambda item: item.sort_key()
        )
        return result

    def _item_key(self, item):
        if item.item_type == "task":
            return (
                "task",
                item.summary.strip().lower(),
                item.event_date,
            )

        if item.event_id:
            return (
                "event-id",
                item.event_id,
                item.event_date,
            )

        start_time = (
            item.start.strftime("%H:%M")
            if isinstance(item.start, datetime)
            else "ALL_DAY"
        )
        end_time = (
            item.end.strftime("%H:%M")
            if isinstance(item.end, datetime)
            else ""
        )

        return (
            "event",
            item.summary.strip().lower(),
            item.event_date,
            start_time,
            end_time,
        )

    def create_event(self, event):
        if event.item_type == "task":
            return self.tasks_service.create_task(
                event
            )

        return self.calendar_api.create_event(
            event
        )
