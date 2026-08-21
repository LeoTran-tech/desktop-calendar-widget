import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(
        "http://127.0.0.1:9222"
    )

    context = browser.contexts[0]

    page = next(
        page
        for page in context.pages
        if "calendar.google.com" in page.url
    )

    buttons = page.locator('div[role="button"]')

    results = []

    for i in range(buttons.count()):
        button = buttons.nth(i)

        text = button.inner_text().strip()

        if "task:" not in text.lower():
            continue

        data = button.evaluate("""
        el => {
            const cell = el.closest('[role="gridcell"]');

            return {
                button_text: el.innerText,
                button_aria: el.getAttribute("aria-label"),
                button_title: el.getAttribute("title"),
                button_html: el.outerHTML,

                gridcell_text: cell
                    ? cell.innerText
                    : null,

                gridcell_aria: cell
                    ? cell.getAttribute("aria-label")
                    : null
            };
        }
        """)

        results.append(data)

    print("TASK ELEMENTS FOUND:", len(results))

    for i, item in enumerate(results):
        print(f"\n========== TASK #{i} ==========")
        print(json.dumps(
            item,
            indent=2,
            ensure_ascii=False
        ))

    with open(
        "task_dom_dump.json",
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False,
        )

    print("\nSaved: task_dom_dump.json")