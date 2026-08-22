import json
import os
from datetime import date
from pathlib import Path

from playwright.sync_api import sync_playwright

from services.chrome_calendar_session import (
    ensure_calendar_chrome,
)


CALENDAR_URL = (
    "https://calendar.google.com/calendar/u/0/r"
)


def dump_task_structure():
    print("Starting Calendar browser...")

    ensure_calendar_chrome()

    today = date.today()

    url = (
        f"{CALENDAR_URL}/month/"
        f"{today.year}/"
        f"{today.month}/1"
    )

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(
            "http://127.0.0.1:9222",
            timeout=30_000,
        )

        context = browser.contexts[0]

        page = next(
            (
                existing_page
                for existing_page in context.pages
                if "calendar.google.com"
                in existing_page.url
            ),
            None,
        )

        if page is None:
            page = context.new_page()

        print("Opening:", url)

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=15_000,
        )

        page.wait_for_timeout(3000)

        print("Current URL:", page.url)

        if "accounts.google.com" in page.url:
            raise RuntimeError(
                "Google Calendar browser is not signed in."
            )

        buttons = page.locator(
            'div[role="button"]'
        )

        total_buttons = buttons.count()

        print(
            "Total role=button elements:",
            total_buttons,
        )

        task_nodes = []

        for index in range(total_buttons):
            button = buttons.nth(index)

            try:
                canonical = button.evaluate(
                    """
                    el => {
                        const spans = [
                            ...el.querySelectorAll("span")
                        ];

                        const target = spans.find(
                            span =>
                                span.innerText &&
                                span.innerText
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

                if not canonical:
                    continue

                print(
                    "FOUND TASK:",
                    canonical,
                )

                outer_html = button.evaluate(
                    "el => el.outerHTML"
                )

                parent_html = button.evaluate(
                    """
                    el =>
                        el.parentElement
                        ? el.parentElement.outerHTML
                        : null
                    """
                )

                attributes = button.evaluate(
                    """
                    el => {
                        const result = {};

                        for (
                            const attr of el.attributes
                        ) {
                            result[attr.name] =
                                attr.value;
                        }

                        return result;
                    }
                    """
                )

                try:
                    aria_snapshot = (
                        button.aria_snapshot()
                    )
                except Exception as exc:
                    aria_snapshot = (
                        f"ARIA snapshot failed: {exc}"
                    )

                task_nodes.append(
                    {
                        "index": index,
                        "canonical_text": canonical,
                        "attributes": attributes,
                        "outer_html": outer_html,
                        "parent_html": parent_html,
                        "aria_snapshot": aria_snapshot,
                    }
                )

            except Exception as exc:
                print(
                    "Could not inspect button",
                    index,
                    repr(exc),
                )

        dump = {
            "url": page.url,
            "month": today.strftime(
                "%Y-%m"
            ),
            "total_role_buttons":
                total_buttons,
            "task_nodes_found":
                len(task_nodes),
            "task_nodes":
                task_nodes,
        }

        output_dir = (
            Path(
                os.environ["LOCALAPPDATA"]
            )
            / "DesktopCalendar"
            / "Diagnostics"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = (
            output_dir
            / "task_dom_dump.json"
        )

        output_file.write_text(
            json.dumps(
                dump,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print()
        print("==============================")
        print(
            "Tasks found:",
            len(task_nodes),
        )
        print(
            "Saved:",
            output_file,
        )
        print("==============================")


if __name__ == "__main__":
    dump_task_structure()