import re
from datetime import date, datetime

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


def parse_time(value: str):
    normalized = (
        value.strip()
        .upper()
        .replace(" ", "")
    )

    return datetime.strptime(
        normalized,
        "%I:%M%p"
        if ":" in normalized
        else "%I%p",
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
            browser = p.chromium.connect_over_cdp(
                "http://127.0.0.1:9222",
                timeout=10_000,
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
                while current_month <= last_month:
                    self._open_month(
                        page,
                        current_month,
                    )

                    if "accounts.google.com" in page.url:
                        raise RuntimeError(
                            "Google Calendar browser is not signed in. "
                            "Open Settings and sign in to Google Calendar."
                        )

                    for task in self._scrape_visible_tasks(
                        page,
                        start_date,
                        end_date,
                    ):
                        key = (
                            task.summary
                            .strip()
                            .lower(),
                            task.event_date,
                        )
                        results[key] = task

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

        output = list(
            results.values()
        )
        output.sort(
            key=lambda item: item.sort_key()
        )
        return output

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
            wait_until="domcontentloaded",
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
    ) -> list[CalendarEvent]:
        results: list[CalendarEvent] = []

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
                canonical = button.evaluate(
                    """
                    el => {
                        const spans = [
                            ...el.querySelectorAll("span")
                        ];

                        const target = spans.find(
                            span => span.innerText
                                && span.innerText
                                    .trim()
                                    .toLowerCase()
                                    .startsWith("task:")
                        );

                        return target
                            ? target.innerText.trim()
                            : null;
                    }
                    """
                )
            except Exception:
                continue

            if not canonical:
                continue

            match = TASK_PATTERN.match(
                canonical
            )

            if not match:
                continue

            task_date = datetime.strptime(
                match.group("date"),
                "%B %d, %Y",
            ).date()

            if not (
                start_date
                <= task_date
                < end_date
            ):
                continue

            title = match.group(
                "title"
            ).strip()

            time_text = match.group(
                "time"
            ).strip()

            if time_text.lower() == "all day":
                start = task_date
                end = None
            else:
                parts = re.split(
                    r"\s+to\s+",
                    time_text,
                    flags=re.IGNORECASE,
                )

                start = datetime.combine(
                    task_date,
                    parse_time(
                        parts[0]
                    ),
                )
                end = None

                if len(parts) == 2:
                    end = datetime.combine(
                        task_date,
                        parse_time(
                            parts[1]
                        ),
                    )

            results.append(
                CalendarEvent(
                    summary=title,
                    start=start,
                    end=end,
                    item_type="task",
                )
            )

        return results
