import re
from datetime import datetime, timedelta

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


def parse_time(value):
    value = value.strip().upper()

    return datetime.strptime(
        value,
        "%I:%M%p" if ":" in value else "%I%p",
    ).time()


class GoogleCalendarScraperService:

    def get_tasks(self, days_ahead=14):
        ensure_calendar_chrome()
        today = datetime.now().date()
        end_date = today + timedelta(days=days_ahead)

        results = []

        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(
                "http://127.0.0.1:9222"
            )

            context = browser.contexts[0]

            page = next(
                (
                    page
                    for page in context.pages
                    if "calendar.google.com" in page.url
                ),
                None,
            )

            if page is None:
                page = context.new_page()

                page.goto(
                    "https://calendar.google.com/calendar/u/0/r",
                    wait_until="domcontentloaded",
                )

            page.wait_for_timeout(3000)
            
            buttons = page.locator('div[role="button"]')

            for i in range(buttons.count()):
                button = buttons.nth(i)

                canonical = button.evaluate("""
                el => {
                    const spans = [...el.querySelectorAll("span")];

                    const target = spans.find(
                        span => span.innerText
                            && span.innerText.trim()
                                .toLowerCase()
                                .startsWith("task:")
                    );

                    return target
                        ? target.innerText.trim()
                        : null;
                }
                """)

                if not canonical:
                    continue

                match = TASK_PATTERN.match(canonical)

                if not match:
                    continue

                title = match.group("title").strip()

                task_date = datetime.strptime(
                    match.group("date"),
                    "%B %d, %Y",
                ).date()

                if not (today <= task_date < end_date):
                    continue

                time_text = match.group("time").strip()

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
                        parse_time(parts[0]),
                    )

                    end = None

                    if len(parts) == 2:
                        end = datetime.combine(
                            task_date,
                            parse_time(parts[1]),
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