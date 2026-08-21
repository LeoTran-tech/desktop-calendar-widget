from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import requests

from utils.app_settings import AppSettings


CDP_PORT = 9222
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"

CALENDAR_URL = (
    "https://calendar.google.com/calendar/u/0/r"
)

APP_DATA_DIR = (
    Path(os.environ["LOCALAPPDATA"])
    / "DesktopCalendar"
)

BROWSER_PROFILES_DIR = (
    APP_DATA_DIR
    / "BrowserProfiles"
)

LEGACY_CHROME_PROFILE_DIR = (
    APP_DATA_DIR
    / "ChromeProfile"
)

OLD_TEMP_PROFILE_DIR = (
    Path(os.environ.get("TEMP", ""))
    / "calendar-debug-profile"
)

BROWSER_NAMES = {
    "edge": "Microsoft Edge",
    "chrome": "Google Chrome",
    "brave": "Brave",
}


def _candidate_paths(
    browser: str,
) -> list[Path]:
    local_app_data = Path(
        os.environ.get(
            "LOCALAPPDATA",
            "",
        )
    )
    program_files = Path(
        os.environ.get(
            "PROGRAMFILES",
            r"C:\Program Files",
        )
    )
    program_files_x86 = Path(
        os.environ.get(
            "PROGRAMFILES(X86)",
            r"C:\Program Files (x86)",
        )
    )

    if browser == "edge":
        return [
            program_files_x86
            / "Microsoft"
            / "Edge"
            / "Application"
            / "msedge.exe",
            program_files
            / "Microsoft"
            / "Edge"
            / "Application"
            / "msedge.exe",
            local_app_data
            / "Microsoft"
            / "Edge"
            / "Application"
            / "msedge.exe",
        ]

    if browser == "chrome":
        return [
            program_files
            / "Google"
            / "Chrome"
            / "Application"
            / "chrome.exe",
            program_files_x86
            / "Google"
            / "Chrome"
            / "Application"
            / "chrome.exe",
            local_app_data
            / "Google"
            / "Chrome"
            / "Application"
            / "chrome.exe",
        ]

    if browser == "brave":
        return [
            program_files
            / "BraveSoftware"
            / "Brave-Browser"
            / "Application"
            / "brave.exe",
            program_files_x86
            / "BraveSoftware"
            / "Brave-Browser"
            / "Application"
            / "brave.exe",
            local_app_data
            / "BraveSoftware"
            / "Brave-Browser"
            / "Application"
            / "brave.exe",
        ]

    return []


def find_browser_executable(
    browser: str,
) -> Path | None:
    browser = browser.lower()

    for path in _candidate_paths(
        browser
    ):
        if path.exists():
            return path

    return None


def browser_display_name(
    browser: str,
) -> str:
    return BROWSER_NAMES.get(
        browser.lower(),
        browser.title(),
    )


def browser_debugging_running() -> bool:
    try:
        response = requests.get(
            f"{CDP_URL}/json/version",
            timeout=1,
        )
        return response.ok
    except requests.RequestException:
        return False


def chrome_debugging_running() -> bool:
    """Compatibility name retained for older code."""
    return browser_debugging_running()


def calendar_browser_signed_in() -> bool:
    """Return True when the app-owned browser has an open Calendar page."""

    if not browser_debugging_running():
        return False

    try:
        response = requests.get(
            f"{CDP_URL}/json",
            timeout=2,
        )
        response.raise_for_status()
        targets = response.json()
    except (requests.RequestException, ValueError):
        return False

    for target in targets:
        url = str(
            target.get(
                "url",
                "",
            )
        ).lower()

        if (
            "calendar.google.com" in url
            and "accounts.google.com" not in url
        ):
            return True

    return False


def _new_profile_dir(
    browser: str,
) -> Path:
    return (
        BROWSER_PROFILES_DIR
        / browser.lower()
    )


def profile_dir_for_browser(
    browser: str,
) -> Path:
    browser = browser.lower()

    if (
        browser == "chrome"
        and LEGACY_CHROME_PROFILE_DIR.exists()
        and not _new_profile_dir("chrome").exists()
    ):
        return LEGACY_CHROME_PROFILE_DIR

    return _new_profile_dir(
        browser
    )


def _migrate_very_old_chrome_profile() -> None:
    if (
        not OLD_TEMP_PROFILE_DIR.exists()
        or LEGACY_CHROME_PROFILE_DIR.exists()
        or _new_profile_dir("chrome").exists()
    ):
        return

    LEGACY_CHROME_PROFILE_DIR.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:
        shutil.move(
            str(OLD_TEMP_PROFILE_DIR),
            str(LEGACY_CHROME_PROFILE_DIR),
        )
    except Exception as exc:
        print(
            "Could not migrate old Chrome profile:",
            exc,
        )


def migrate_old_profile() -> None:
    _migrate_very_old_chrome_profile()


def selected_browser() -> str:
    return AppSettings().get_browser()


def launch_calendar_browser(
    browser: str | None = None,
    *,
    headless: bool,
) -> None:
    """Launch the chosen Chromium browser using an app-owned profile."""

    browser = (
        browser
        or selected_browser()
    ).lower()

    if browser not in AppSettings.BROWSER_OPTIONS:
        browser = AppSettings.DEFAULT_BROWSER

    if browser_debugging_running():
        return

    if browser == "chrome":
        _migrate_very_old_chrome_profile()

    executable = find_browser_executable(
        browser
    )

    if executable is None:
        raise FileNotFoundError(
            f"{browser_display_name(browser)} was not found. "
            "Install it or choose another browser in Desktop Calendar Settings."
        )

    profile_dir = profile_dir_for_browser(
        browser
    )
    profile_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    arguments = [
        str(executable),
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={profile_dir}",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
    ]

    if headless:
        arguments.extend(
            [
                "--headless=new",
                "--window-size=1600,1200",
            ]
        )

    arguments.append(
        CALENDAR_URL
    )

    subprocess.Popen(
        arguments,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(40):
        if browser_debugging_running():
            return

        time.sleep(0.5)

    raise RuntimeError(
        f"{browser_display_name(browser)} started, "
        f"but remote debugging port {CDP_PORT} did not become available."
    )


def stop_calendar_browser() -> None:
    """Stop only the browser process owned by Desktop Calendar."""

    if not browser_debugging_running():
        return

    powershell_command = f"""
    Get-CimInstance Win32_Process |
    Where-Object {{
        $_.CommandLine -and
        $_.CommandLine -like '*--remote-debugging-port={CDP_PORT}*' -and
        $_.CommandLine -like '*DesktopCalendar*'
    }} |
    ForEach-Object {{
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }}
    """

    creation_flags = getattr(
        subprocess,
        "CREATE_NO_WINDOW",
        0,
    )

    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-WindowStyle",
            "Hidden",
            "-Command",
            powershell_command,
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=creation_flags,
        check=False,
    )

    for _ in range(30):
        if not browser_debugging_running():
            return

        time.sleep(0.2)

    raise RuntimeError(
        "Desktop Calendar could not stop its background browser."
    )


def open_calendar_browser_for_login(
    browser: str,
) -> None:
    """Switch the app-owned browser from headless mode to visible sign-in."""

    browser = browser.lower()

    stop_calendar_browser()

    launch_calendar_browser(
        browser,
        headless=False,
    )


def ensure_calendar_chrome() -> None:
    """Ensure the selected browser is available for the existing scraper."""

    launch_calendar_browser(
        selected_browser(),
        headless=True,
    )
