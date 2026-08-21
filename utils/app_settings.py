from __future__ import annotations

from PySide6.QtCore import QByteArray, QSettings


class AppSettings:
    """Stores lightweight user preferences outside the project folder."""

    ORGANIZATION = "LeoTran"
    APPLICATION = "DesktopCalendar"

    UPCOMING_DAY_OPTIONS = (3, 7, 14, 30)
    DEFAULT_UPCOMING_DAYS = 7

    BROWSER_OPTIONS = ("edge", "chrome", "brave")
    DEFAULT_BROWSER = "edge"

    def __init__(self) -> None:
        self._settings = QSettings(
            self.ORGANIZATION,
            self.APPLICATION,
        )

    def get_upcoming_days(self) -> int:
        value = self._settings.value(
            "calendar/upcoming_days",
            self.DEFAULT_UPCOMING_DAYS,
        )

        try:
            value = int(value)
        except (TypeError, ValueError):
            value = self.DEFAULT_UPCOMING_DAYS

        if value not in self.UPCOMING_DAY_OPTIONS:
            return self.DEFAULT_UPCOMING_DAYS

        return value

    def set_upcoming_days(self, days: int) -> None:
        if days not in self.UPCOMING_DAY_OPTIONS:
            raise ValueError(
                f"Upcoming days must be one of {self.UPCOMING_DAY_OPTIONS}."
            )

        self._settings.setValue(
            "calendar/upcoming_days",
            days,
        )

    def has_browser_preference(self) -> bool:
        return self._settings.contains(
            "browser/preferred"
        )

    def get_browser(self) -> str:
        value = str(
            self._settings.value(
                "browser/preferred",
                self.DEFAULT_BROWSER,
            )
            or self.DEFAULT_BROWSER
        ).lower()

        if value not in self.BROWSER_OPTIONS:
            return self.DEFAULT_BROWSER

        return value

    def set_browser(self, browser: str) -> None:
        browser = browser.lower()

        if browser not in self.BROWSER_OPTIONS:
            raise ValueError(
                f"Browser must be one of {self.BROWSER_OPTIONS}."
            )

        self._settings.setValue(
            "browser/preferred",
            browser,
        )

    def is_setup_complete(self) -> bool:
        value = self._settings.value(
            "setup/completed",
            False,
        )

        if isinstance(value, str):
            return value.lower() in (
                "1",
                "true",
                "yes",
            )

        return bool(value)

    def set_setup_complete(
        self,
        completed: bool,
    ) -> None:
        self._settings.setValue(
            "setup/completed",
            bool(completed),
        )

    def get_window_geometry(self) -> QByteArray | None:
        value = self._settings.value(
            "window/geometry",
            None,
        )

        if isinstance(value, QByteArray):
            return value

        if isinstance(value, (bytes, bytearray)):
            return QByteArray(value)

        return None

    def set_window_geometry(self, geometry: QByteArray) -> None:
        self._settings.setValue(
            "window/geometry",
            geometry,
        )

    def get_screen_name(self) -> str:
        return str(
            self._settings.value(
                "window/screen_name",
                "",
            )
            or ""
        )

    def set_screen_name(self, name: str) -> None:
        self._settings.setValue(
            "window/screen_name",
            name,
        )

    def sync(self) -> None:
        self._settings.sync()
