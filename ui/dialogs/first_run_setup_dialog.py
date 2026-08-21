from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from services.chrome_calendar_session import (
    browser_display_name,
    calendar_browser_signed_in,
    find_browser_executable,
    open_calendar_browser_for_login,
    stop_calendar_browser,
)
from services.google_auth import get_google_credentials
from utils.app_settings import AppSettings


class FirstRunSetupDialog(QDialog):
    """Required one-time setup before the desktop widget is started."""

    def __init__(
        self,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.settings = AppSettings()
        self.google_connected = False
        self.browser_verified = False

        self.setWindowTitle(
            "Set up Desktop Calendar"
        )
        self.setModal(True)
        self.setMinimumWidth(470)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        title = QLabel(
            "Welcome to Desktop Calendar"
        )
        title.setStyleSheet(
            "font-size: 19px; font-weight: 600;"
        )
        layout.addWidget(title)

        intro = QLabel(
            "Complete these two sign-ins once. Desktop Calendar will then "
            "start normally and refresh in the background."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        # ------------------------------------------------------------
        # Step 1: Google OAuth for Calendar API + Tasks API
        # ------------------------------------------------------------

        oauth_title = QLabel(
            "1. Connect your Google account"
        )
        oauth_title.setStyleSheet(
            "font-size: 15px; font-weight: 600;"
        )
        layout.addWidget(oauth_title)

        oauth_text = QLabel(
            "This gives Desktop Calendar permission to read Google Calendar "
            "events and Google Tasks."
        )
        oauth_text.setWordWrap(True)
        layout.addWidget(oauth_text)

        oauth_row = QHBoxLayout()

        self.google_button = QPushButton(
            "Sign in with Google"
        )
        self.google_button.clicked.connect(
            self._connect_google
        )
        oauth_row.addWidget(
            self.google_button
        )

        self.google_status = QLabel(
            "Not connected"
        )
        oauth_row.addWidget(
            self.google_status,
            1,
        )

        layout.addLayout(
            oauth_row
        )

        # ------------------------------------------------------------
        # Step 2: Browser profile for recurring-task scraping
        # ------------------------------------------------------------

        browser_title = QLabel(
            "2. Connect Google Calendar for recurring tasks"
        )
        browser_title.setStyleSheet(
            "font-size: 15px; font-weight: 600;"
        )
        layout.addWidget(browser_title)

        browser_text = QLabel(
            "Google's Tasks API does not expose everything shown in Calendar. "
            "Choose a Chromium browser so Desktop Calendar can read that extra "
            "task information from a separate app-owned profile."
        )
        browser_text.setWordWrap(True)
        layout.addWidget(browser_text)

        self.browser_combo = QComboBox()

        labels = {
            "edge": "Microsoft Edge (recommended)",
            "chrome": "Google Chrome",
            "brave": "Brave",
        }

        for browser in AppSettings.BROWSER_OPTIONS:
            installed = (
                find_browser_executable(browser)
                is not None
            )

            text = labels[browser]

            if not installed:
                text += " — not found"

            self.browser_combo.addItem(
                text,
                browser,
            )

        default_index = (
            self.browser_combo.findData(
                AppSettings.DEFAULT_BROWSER
            )
        )

        if default_index >= 0:
            self.browser_combo.setCurrentIndex(
                default_index
            )

        self.browser_combo.currentIndexChanged.connect(
            self._browser_changed
        )
        self.browser_combo.setEnabled(False)

        layout.addWidget(
            self.browser_combo
        )

        browser_buttons = QHBoxLayout()

        self.browser_login_button = QPushButton(
            "Open browser to sign in"
        )
        self.browser_login_button.setEnabled(
            False
        )
        self.browser_login_button.clicked.connect(
            self._open_browser_login
        )
        browser_buttons.addWidget(
            self.browser_login_button
        )

        self.browser_check_button = QPushButton(
            "Check sign-in"
        )
        self.browser_check_button.setEnabled(
            False
        )
        self.browser_check_button.clicked.connect(
            self._check_browser_login
        )
        browser_buttons.addWidget(
            self.browser_check_button
        )

        layout.addLayout(
            browser_buttons
        )

        self.browser_status = QLabel(
            "Complete Google account sign-in first."
        )
        self.browser_status.setWordWrap(True)
        layout.addWidget(
            self.browser_status
        )

        help_text = QLabel(
            "When the browser opens, sign in until Google Calendar itself is "
            "visible. Keep that browser window open, return here, and click "
            "\"Check sign-in\"."
        )
        help_text.setWordWrap(True)
        layout.addWidget(
            help_text
        )

        # ------------------------------------------------------------
        # Finish / cancel
        # ------------------------------------------------------------

        bottom = QHBoxLayout()
        bottom.addStretch()

        self.cancel_button = QPushButton(
            "Cancel"
        )
        self.cancel_button.clicked.connect(
            self.reject
        )
        bottom.addWidget(
            self.cancel_button
        )

        self.finish_button = QPushButton(
            "Finish setup"
        )
        self.finish_button.setEnabled(
            False
        )
        self.finish_button.clicked.connect(
            self._finish_setup
        )
        bottom.addWidget(
            self.finish_button
        )

        layout.addLayout(
            bottom
        )

    def _selected_browser(self) -> str:
        return str(
            self.browser_combo.currentData()
            or AppSettings.DEFAULT_BROWSER
        )

    def _connect_google(self) -> None:
        self.google_button.setEnabled(
            False
        )
        self.google_status.setText(
            "Waiting for Google sign-in..."
        )

        try:
            credentials = get_google_credentials()
        except Exception as exc:
            self.google_status.setText(
                "Not connected"
            )
            QMessageBox.warning(
                self,
                "Google sign-in failed",
                str(exc),
            )
            self.google_button.setEnabled(
                True
            )
            return

        if not credentials.valid:
            self.google_status.setText(
                "Not connected"
            )
            self.google_button.setEnabled(
                True
            )
            return

        self.google_connected = True
        self.google_status.setText(
            "Connected"
        )
        self.google_button.setText(
            "Google account connected"
        )

        self.browser_combo.setEnabled(
            True
        )
        self.browser_login_button.setEnabled(
            True
        )

        self.browser_status.setText(
            "Choose a browser, then open it to sign in to Google Calendar."
        )

        self._update_finish_state()

    def _browser_changed(self) -> None:
        self.browser_verified = False
        self.browser_check_button.setEnabled(
            False
        )

        if self.google_connected:
            self.browser_status.setText(
                "Open this browser and sign in to Google Calendar."
            )

        self._update_finish_state()

    def _open_browser_login(self) -> None:
        browser = self._selected_browser()

        if find_browser_executable(browser) is None:
            QMessageBox.warning(
                self,
                "Browser not found",
                (
                    f"{browser_display_name(browser)} was not found. "
                    "Install it or choose another browser."
                ),
            )
            return

        try:
            open_calendar_browser_for_login(
                browser
            )
        except Exception as exc:
            QMessageBox.warning(
                self,
                "Browser could not be opened",
                str(exc),
            )
            return

        self.browser_verified = False
        self.browser_check_button.setEnabled(
            True
        )
        self.browser_status.setText(
            "Sign in until Google Calendar is visible, then click Check sign-in."
        )
        self._update_finish_state()

    def _check_browser_login(self) -> None:
        if not calendar_browser_signed_in():
            self.browser_verified = False
            self.browser_status.setText(
                "Google Calendar is not signed in yet."
            )
            QMessageBox.information(
                self,
                "Sign-in not detected",
                (
                    "Desktop Calendar cannot see an authenticated Google "
                    "Calendar page yet.\n\n"
                    "Finish signing in in the browser, leave Google Calendar "
                    "open, then click Check sign-in again."
                ),
            )
            self._update_finish_state()
            return

        self.browser_verified = True
        self.browser_status.setText(
            "Google Calendar sign-in verified."
        )
        self._update_finish_state()

    def _update_finish_state(self) -> None:
        self.finish_button.setEnabled(
            self.google_connected
            and self.browser_verified
        )

    def _finish_setup(self) -> None:
        browser = self._selected_browser()

        self.settings.set_browser(
            browser
        )
        self.settings.set_setup_complete(
            True
        )
        self.settings.sync()

        # Close the one-time visible app-owned browser. The normal widget
        # will relaunch the same profile headlessly when its first refresh runs.
        try:
            stop_calendar_browser()
        except Exception:
            pass

        self.accept()
