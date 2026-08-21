from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from services.chrome_calendar_session import (
    browser_display_name,
    open_calendar_browser_for_login,
)
from utils.app_settings import AppSettings


class SettingsDialog(QDialog):
    def __init__(
        self,
        upcoming_days: int,
        preferred_browser: str = AppSettings.DEFAULT_BROWSER,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle("Desktop Calendar Settings")
        self.setModal(True)
        self.setMinimumWidth(360)

        layout = QVBoxLayout(self)

        description = QLabel(
            "Choose how far ahead the upcoming list should show and which "
            "browser Desktop Calendar should use for recurring-task sync."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        form = QFormLayout()

        self.upcoming_combo = QComboBox()

        labels = {
            3: "3 days",
            7: "7 days (recommended)",
            14: "14 days",
            30: "30 days",
        }

        for days in AppSettings.UPCOMING_DAY_OPTIONS:
            self.upcoming_combo.addItem(labels[days], days)

        index = self.upcoming_combo.findData(upcoming_days)
        if index >= 0:
            self.upcoming_combo.setCurrentIndex(index)

        form.addRow("Upcoming range:", self.upcoming_combo)

        self.browser_combo = QComboBox()
        browser_labels = {
            "edge": "Microsoft Edge (recommended)",
            "chrome": "Google Chrome",
            "brave": "Brave",
        }

        for browser in AppSettings.BROWSER_OPTIONS:
            self.browser_combo.addItem(
                browser_labels[browser],
                browser,
            )

        browser_index = self.browser_combo.findData(
            preferred_browser
        )
        if browser_index < 0:
            browser_index = self.browser_combo.findData(
                AppSettings.DEFAULT_BROWSER
            )
        if browser_index >= 0:
            self.browser_combo.setCurrentIndex(browser_index)

        form.addRow("Calendar browser:", self.browser_combo)
        layout.addLayout(form)

        browser_note = QLabel(
            "Changing browser takes effect after restarting Desktop Calendar. "
            "Each browser uses a separate app-owned profile."
        )
        browser_note.setWordWrap(True)
        layout.addWidget(browser_note)

        self.login_button = QPushButton(
            "Open selected browser for Google sign-in"
        )
        self.login_button.clicked.connect(self._open_for_login)
        layout.addWidget(self.login_button)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def upcoming_days(self) -> int:
        return int(self.upcoming_combo.currentData())

    def browser(self) -> str:
        return str(
            self.browser_combo.currentData()
            or AppSettings.DEFAULT_BROWSER
        )

    def _open_for_login(self) -> None:
        browser = self.browser()

        try:
            open_calendar_browser_for_login(browser)
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Browser could not be opened",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Sign in to Google Calendar",
            (
                f"{browser_display_name(browser)} has been opened with "
                "Desktop Calendar's separate profile.\n\n"
                "Sign in to Google Calendar there. You can then close "
                "the browser and restart Desktop Calendar."
            ),
        )
