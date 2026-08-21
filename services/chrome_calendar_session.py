import os
import shutil
import subprocess
import time
from pathlib import Path

import requests


CDP_URL = "http://127.0.0.1:9222"

CHROME_PATH = Path(
    r"C:\Program Files\Google\Chrome\Application\chrome.exe"
)

# Profile mới: lưu bền trong AppData
PROFILE_DIR = (
    Path(os.environ["LOCALAPPDATA"])
    / "DesktopCalendar"
    / "ChromeProfile"
)

# Profile cũ trong TEMP
OLD_PROFILE_DIR = (
    Path(os.environ["TEMP"])
    / "calendar-debug-profile"
)


def chrome_debugging_running() -> bool:
    try:
        response = requests.get(
            f"{CDP_URL}/json/version",
            timeout=1,
        )
        return response.ok

    except requests.RequestException:
        return False


def migrate_old_profile() -> None:
    """
    Move the old TEMP Chrome profile into LOCALAPPDATA.

    This preserves the existing Google login/session.
    """

    if PROFILE_DIR.exists():
        return

    if OLD_PROFILE_DIR.exists():
        PROFILE_DIR.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        try:
            shutil.move(
                str(OLD_PROFILE_DIR),
                str(PROFILE_DIR),
            )

            print(
                "Chrome profile migrated to:",
                PROFILE_DIR,
            )

        except Exception as exc:
            print(
                "Could not migrate old Chrome profile:",
                exc,
            )

    else:
        PROFILE_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )


def ensure_calendar_chrome() -> None:
    """
    Ensure Chrome is running with remote debugging.

    Uses a persistent Chrome profile so Google login
    survives across app restarts.
    """

    if chrome_debugging_running():
        return

    if not CHROME_PATH.exists():
        raise FileNotFoundError(
            f"Google Chrome not found at: {CHROME_PATH}"
        )

    migrate_old_profile()

    PROFILE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    subprocess.Popen(
        [
            str(CHROME_PATH),

            # Chrome chạy hoàn toàn nền
            "--headless=new",

            "--remote-debugging-port=9222",

            f"--user-data-dir={PROFILE_DIR}",

            "--disable-gpu",

            "--no-first-run",
            "--no-default-browser-check",

            "https://calendar.google.com/calendar/u/0/r",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    # Wait for Chrome's CDP server
    for _ in range(30):
        if chrome_debugging_running():
            return

        time.sleep(0.5)

    raise RuntimeError(
        "Chrome started but remote debugging "
        "port 9222 did not become available."
    )