import json
import os
import re

from datetime import date, datetime
from pathlib import Path

from playwright.sync_api import sync_playwright

from models.calendar_event import CalendarEvent
from services.chrome_calendar_session import (
    ensure_calendar_chrome,
)


TASK_PATTERN = re.compile(
    r"^task:\s*(?P<title>.+),\s*"
    r"(?P<status>Not completed|Completed),\s*"
    r"(?P<date>[A-Za-z]+ \d{1,2}, \d{4}),\s*"
    r"(?P<time>.+)$",
    re.IGNORECASE,
)

CALENDAR_URL = (
    "https://calendar.google.com/calendar/u/0/r"
)


class ScraperStructureError(RuntimeError):
    """Raised when Google Calendar's task structure looks incompatible."""

    pass


def parse_time(value: str):
    normalized = (
        value.strip()
        .upper()
        .replace(" ", "")
    )

    return datetime.strptime(
        normalized,
        (
            "%I:%M%p"
            if ":" in normalized
            else "%I%p"
        ),
    ).time()


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


class GoogleCalendarScraperService:
    """Reads task cards from the Google Calendar month UI."""

    PAGE_SETTLE_MS = 2200
    MAX_ATTEMPTS = 2

    def get_tasks(
        self,
        days_ahead: int = 14,
    ) -> list[CalendarEvent]:
        from datetime import timedelta

        today = datetime.now().date()

        return self.get_tasks_between(
            today,
            today + timedelta(
                days=days_ahead
            ),
        )

    def get_tasks_between(
        self,
        start_date: date,
        end_date: date,
    ) -> list[CalendarEvent]:

        if end_date <= start_date:
            return []

        ensure_calendar_chrome()

        results: dict[
            tuple[str, date],
            CalendarEvent,
        ] = {}

        first_month = month_start(
            start_date
        )

        last_month = month_start(
            end_date
        )

        if end_date.day == 1:
            last_month = add_months(
                last_month,
                -1,
            )

        with sync_playwright() as p:
            browser = (
                p.chromium.connect_over_cdp(
                    "http://127.0.0.1:9222",
                    timeout=10_000,
                )
            )

            context = browser.contexts[0]

            page = next(
                (
                    existing_page
                    for existing_page
                    in context.pages
                    if "calendar.google.com"
                    in existing_page.url
                ),
                None,
            )

            if page is None:
                page = context.new_page()

            current_month = first_month

            try:
                while (
                    current_month
                    <= last_month
                ):
                    scraped_tasks = (
                        self._scrape_month_with_retry(
                            page,
                            current_month,
                            start_date,
                            end_date,
                        )
                    )

                    for task in scraped_tasks:
                        key = (
                            task.summary
                            .strip()
                            .lower(),
                            task.event_date,
                        )

                        results[key] = task

                    current_month = (
                        add_months(
                            current_month,
                            1,
                        )
                    )

            finally:
                today = (
                    datetime.now()
                    .date()
                )

                try:
                    self._open_month(
                        page,
                        month_start(
                            today
                        ),
                        wait=False,
                    )

                except Exception:
                    pass

        output = list(
            results.values()
        )

        output.sort(
            key=lambda item:
                item.sort_key()
        )

        return output

    def _scrape_month_with_retry(
        self,
        page,
        current_month: date,
        start_date: date,
        end_date: date,
    ) -> list[CalendarEvent]:

        last_health = None

        for attempt in range(
            1,
            self.MAX_ATTEMPTS + 1,
        ):
            try:
                self._open_month(
                    page,
                    current_month,
                )

                if (
                    "accounts.google.com"
                    in page.url
                ):
                    raise RuntimeError(
                        "Google Calendar browser "
                        "is not signed in. "
                        "Open Settings and sign in "
                        "to Google Calendar."
                    )

                (
                    scraped_tasks,
                    health,
                ) = (
                    self._scrape_visible_tasks(
                        page,
                        start_date,
                        end_date,
                    )
                )

                last_health = health

                # Google still exposes something
                # beginning with "task:", but the
                # text no longer follows the format
                # understood by TASK_PATTERN.
                if (
                    health[
                        "parse_failures"
                    ]
                    > 0
                ):
                    raise (
                        ScraperStructureError(
                            "Task accessibility "
                            "text was found but "
                            "its format could not "
                            "be parsed."
                        )
                    )

                return scraped_tasks

            except (
                ScraperStructureError
            ) as exc:

                print(
                    f"SCRAPER WARNING "
                    f"{current_month:%Y-%m} "
                    f"attempt "
                    f"{attempt}/"
                    f"{self.MAX_ATTEMPTS}:",
                    exc,
                )

                # Only create the diagnostic
                # snapshot if the retry also
                # failed.
                if (
                    attempt
                    == self.MAX_ATTEMPTS
                ):
                    self._save_diagnostic_snapshot(
                        page=page,
                        current_month=current_month,
                        reason=str(exc),
                        health=last_health,
                    )

                    raise

                # Give transient rendering
                # problems one more chance.
                page.reload(
                    wait_until=(
                        "domcontentloaded"
                    ),
                    timeout=15_000,
                )

                page.wait_for_timeout(
                    2500
                )

        return []
    
    def save_diagnostics_between(
        self,
        start_date: date,
        end_date: date,
        reason: str,
    ) -> None:
        """Save diagnostics for every month in a suspicious range."""

        if end_date <= start_date:
            return

        ensure_calendar_chrome()

        first_month = month_start(
            start_date
        )

        last_month = month_start(
            end_date
        )

        if end_date.day == 1:
            last_month = add_months(
                last_month,
                -1,
            )

        with sync_playwright() as p:
            browser = (
                p.chromium.connect_over_cdp(
                    "http://127.0.0.1:9222",
                    timeout=10_000,
                )
            )

            context = browser.contexts[0]

            page = next(
                (
                    existing_page
                    for existing_page
                    in context.pages
                    if "calendar.google.com"
                    in existing_page.url
                ),
                None,
            )

            if page is None:
                page = context.new_page()

            current_month = first_month

            try:
                while (
                    current_month
                    <= last_month
                ):
                    health = None

                    try:
                        self._open_month(
                            page,
                            current_month,
                        )

                        _, health = (
                            self._scrape_visible_tasks(
                                page,
                                start_date,
                                end_date,
                            )
                        )

                    except Exception as exc:
                        health = {
                            "diagnostic_error":
                                repr(exc),
                        }

                    self._save_diagnostic_snapshot(
                        page=page,
                        current_month=current_month,
                        reason=reason,
                        health=health,
                    )

                    current_month = add_months(
                        current_month,
                        1,
                    )

            finally:
                today = datetime.now().date()

                try:
                    self._open_month(
                        page,
                        month_start(today),
                        wait=False,
                    )
                except Exception:
                    pass

    def _save_diagnostic_snapshot(
        self,
        page,
        current_month: date,
        reason: str,
        health: dict | None,
    ) -> None:
        """
        Save a local diagnostic file when the
        scraper detects an incompatible Google
        Calendar task structure.
        """

        try:
            diagnostic_nodes = []

            buttons = page.locator(
                'div[role="button"]'
            )

            total_buttons = (
                buttons.count()
            )

            for index in range(
                total_buttons
            ):
                button = buttons.nth(
                    index
                )

                try:
                    information = (
                        button.evaluate(
                            """
                            el => {
                                const spans = [
                                    ...el.querySelectorAll(
                                        "span"
                                    )
                                ];

                                const taskSpan =
                                    spans.find(
                                        span =>
                                            span.innerText
                                            &&
                                            span.innerText
                                                .trim()
                                                .toLowerCase()
                                                .startsWith(
                                                    "task:"
                                                )
                                    );

                                if (!taskSpan) {
                                    return null;
                                }

                                const attrs = {};

                                for (
                                    const attr
                                    of el.attributes
                                ) {
                                    attrs[
                                        attr.name
                                    ] = attr.value;
                                }

                                return {
                                    canonical_text:
                                        taskSpan
                                            .innerText
                                            .trim(),

                                    attributes:
                                        attrs,

                                    outer_html:
                                        el.outerHTML,

                                    parent_html:
                                        el.parentElement
                                            ? el
                                                .parentElement
                                                .outerHTML
                                            : null
                                };
                            }
                            """
                        )
                    )

                    if not information:
                        continue

                    try:
                        aria_snapshot = (
                            button
                            .aria_snapshot()
                        )

                    except Exception as exc:
                        aria_snapshot = (
                            "ARIA snapshot "
                            "failed: "
                            f"{exc}"
                        )

                    information[
                        "index"
                    ] = index

                    information[
                        "aria_snapshot"
                    ] = aria_snapshot

                    diagnostic_nodes.append(
                        information
                    )

                except Exception as exc:
                    diagnostic_nodes.append(
                        {
                            "index": index,
                            "inspection_error":
                                repr(exc),
                        }
                    )

            snapshot = {
                "created_at": (
                    datetime.now()
                    .astimezone()
                    .isoformat()
                ),
                "reason": reason,
                "url": page.url,
                "month": (
                    current_month
                    .isoformat()
                ),
                "health": health,
                "total_role_buttons":
                    total_buttons,
                "task_nodes":
                    diagnostic_nodes,
                "page_html_sample": page.locator(
                    "body"
                ).inner_text()[:10000],
            }

            output_dir = (
                Path(
                    os.environ[
                        "LOCALAPPDATA"
                    ]
                )
                / "DesktopCalendar"
                / "Diagnostics"
            )

            output_dir.mkdir(
                parents=True,
                exist_ok=True,
            )

            timestamp = (
                datetime.now()
                .strftime(
                    "%Y%m%d_%H%M%S"
                )
            )

            output_file = (
                output_dir
                / (
                    "scraper_failure_"
                    f"{current_month:%Y_%m}_"
                    f"{timestamp}.json"
                )
            )

            output_file.write_text(
                json.dumps(
                    snapshot,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            print(
                "SCRAPER DIAGNOSTIC SAVED:",
                output_file,
            )

        except Exception as exc:
            # Diagnostic generation itself
            # must never crash the application.
            print(
                "Could not save scraper "
                "diagnostic:",
                repr(exc),
            )

    def _open_month(
        self,
        page,
        target_month: date,
        wait: bool = True,
    ) -> None:

        url = (
            f"{CALENDAR_URL}/month/"
            f"{target_month.year}/"
            f"{target_month.month}/1"
        )

        page.goto(
            url,
            wait_until=(
                "domcontentloaded"
            ),
            timeout=10_000,
        )

        if wait:
            page.wait_for_timeout(
                self.PAGE_SETTLE_MS
            )

    def _scrape_visible_tasks(
        self,
        page,
        start_date: date,
        end_date: date,
    ) -> tuple[
        list[CalendarEvent],
        dict[str, int],
    ]:

        results: list[
            CalendarEvent
        ] = []

        # Diagnostic-only signal.
        # Do NOT treat zero containers as
        # scraper failure because Google uses
        # different DOM variants.
        task_containers = (
            page.locator(
                '[data-eventchip]'
                '[data-eventid^="tasks_"]'
            )
        )

        container_count = (
            task_containers.count()
        )

        candidate_count = 0
        parse_failure_count = 0

        buttons = page.locator(
            'div[role="button"]'
        )

        for index in range(
            buttons.count()
        ):
            button = buttons.nth(
                index
            )

            try:
                canonical = (
                    button.evaluate(
                        """
                        el => {
                            const spans = [
                                ...el.querySelectorAll(
                                    "span"
                                )
                            ];

                            const target =
                                spans.find(
                                    span =>
                                        span.innerText
                                        &&
                                        span.innerText
                                            .trim()
                                            .toLowerCase()
                                            .startsWith(
                                                "task:"
                                            )
                                );

                            return target
                                ? target
                                    .innerText
                                    .trim()
                                : null;
                        }
                        """
                    )
                )

            except Exception:
                continue

            if not canonical:
                continue

            candidate_count += 1

            match = TASK_PATTERN.match(
                canonical
            )

            if not match:
                parse_failure_count += 1
                continue

            task_date = (
                datetime.strptime(
                    match.group(
                        "date"
                    ),
                    "%B %d, %Y",
                )
                .date()
            )

            if not (
                start_date
                <= task_date
                < end_date
            ):
                continue

            title = (
                match.group(
                    "title"
                )
                .strip()
            )

            time_text = (
                match.group(
                    "time"
                )
                .strip()
            )

            if (
                time_text.lower()
                == "all day"
            ):
                start = task_date
                end = None

            else:
                parts = re.split(
                    r"\s+to\s+",
                    time_text,
                    flags=re.IGNORECASE,
                )

                start = (
                    datetime.combine(
                        task_date,
                        parse_time(
                            parts[0]
                        ),
                    )
                )

                end = None

                if len(parts) == 2:
                    end = (
                        datetime.combine(
                            task_date,
                            parse_time(
                                parts[1]
                            ),
                        )
                    )

            results.append(
                CalendarEvent(
                    summary=title,
                    start=start,
                    end=end,
                    item_type="task",
                )
            )

        health = {
            "task_containers":
                container_count,
            "task_candidates":
                candidate_count,
            "parsed_tasks":
                len(results),
            "parse_failures":
                parse_failure_count,
        }

        return results, health