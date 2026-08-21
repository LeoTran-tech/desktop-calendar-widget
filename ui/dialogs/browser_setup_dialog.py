from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from services.chrome_calendar_session import (
    browser_display_name,
    find_browser_executable,
    open_calendar_browser_for_login,
)
from utils.app_settings import AppSettings


class BrowserSetupDialog(QDialog):
    """First-run browser choice for the Calendar task scraper."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        self.setWindowTitle("Calendar Browser Setup")
        self.setModal(True)
        self.setMinimumWidth(390)

        layout = QVBoxLayout(self)

        title = QLabel("Choose a browser for calendar sync")
        title.setStyleSheet(
            "font-size: 16px; font-weight: 600;"
        )
        layout.addWidget(title)

        description = QLabel(
            "Desktop Calendar uses a separate browser profile only for "
            "reading task information that Google does not provide through "
            "the Tasks API. Microsoft Edge is the default."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        self.browser_combo = QComboBox()

        labels = {
            "edge": "Microsoft Edge (recommended)",
            "chrome": "Google Chrome",
            "brave": "Brave",
        }

        for browser in AppSettings.BROWSER_OPTIONS:
            installed = find_browser_executable(browser) is not None
            text = labels[browser]
            if not installed:
                text += " — not found"
            self.browser_combo.addItem(text, browser)

        edge_index = self.browser_combo.findData(
            AppSettings.DEFAULT_BROWSER
        )
        if edge_index >= 0:
            self.browser_combo.setCurrentIndex(edge_index)

        layout.addWidget(self.browser_combo)

        login_note = QLabel(
            "For recurring task support, open the selected browser once, "
            "sign in to Google Calendar, then return here. The app uses its "
            "own browser profile; it does not modify your normal browser profile."
        )
        login_note.setWordWrap(True)
        layout.addWidget(login_note)

        self.login_button = QPushButton(
            "Open Google Calendar for sign-in"
        )
        self.login_button.clicked.connect(
            self._open_for_login
        )
        layout.addWidget(self.login_button)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.button(QDialogButtonBox.Ok).setText(
            "Finish setup"
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_browser(self) -> str:
        return str(
            self.browser_combo.currentData()
            or AppSettings.DEFAULT_BROWSER
        )

    def _open_for_login(self) -> None:
        browser = self.selected_browser()

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
                "Sign in to Google Calendar there. When Calendar is visible, "
                "you can close the browser and click Finish setup."
            ),
        )
