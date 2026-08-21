from datetime import date, datetime

from PySide6.QtCore import QTimer, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices, QHideEvent, QShowEvent
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QWidget,
)

from controllers.calendar_controller import CalendarController
from models.calendar_event import CalendarEvent
from services.combined_calendar import CombinedCalendarService
from services.event_cache import EventCache
from ui.behaviors.frameless_window import FramelessWindowBehavior
from ui.behaviors.window_position import WindowPositionManager
from ui.components.month_calendar import MonthCalendar
from ui.components.upcoming_events import UpcomingEventsPanel
from ui.dialogs.settings_dialog import SettingsDialog
from ui.styles import OUTER_CONTAINER_STYLE
from utils.app_settings import AppSettings


class CalendarWidget(
    FramelessWindowBehavior,
    QWidget,
):
    """Top-level desktop calendar window."""

    REFRESH_INTERVAL_MS = 5 * 60_000

    visibility_changed = Signal(bool)

    def __init__(self) -> None:
        super().__init__()

        self.settings = AppSettings()
        self.upcoming_days = (
            self.settings.get_upcoming_days()
        )

        self.preferred_browser = (
            self.settings.get_browser()
        )

        self.service = CombinedCalendarService()

        self.controller = CalendarController(
            self.service,
            self,
        )

        self.cache = EventCache()
        self.last_successful_update = None
        self.sync_failed = False
        self.cache_updated_at = None
        self.has_cached_events = False

        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._setup_timer()
        self._init_frameless_behavior()

        self.position_manager = (
            WindowPositionManager(
                self,
                self.settings,
            )
        )
        self.position_manager.restore()

        self._load_cached_events()
        self.controller.refresh()


    # ================================================================
    # CACHE / STARTUP
    # ================================================================

    def _load_cached_events(self) -> None:
        events = self.cache.load()
        self.cache_updated_at = (
            self.cache.get_updated_at()
        )

        if not events:
            return

        self.has_cached_events = True

        self.month_calendar.set_events(events)
        self.upcoming_events.set_events(events)

        if self.cache_updated_at:
            self.last_successful_update = (
                self.cache_updated_at.astimezone()
            )
            self.upcoming_events.set_sync_status(
                self._saved_status_text(
                    self.last_successful_update
                )
            )

    # ================================================================
    # WINDOW
    # ================================================================

    def _setup_window(self) -> None:
        self.setWindowTitle("Desktop Calendar")

        # Desktop-style utility window: no normal taskbar button.
        self.setWindowFlags(
            Qt.Tool
            | Qt.FramelessWindowHint
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground
        )

        self.resize(850, 320)
        self.setMinimumSize(650, 300)
        self.setMouseTracking(True)

    def showEvent(
        self,
        event: QShowEvent,
    ) -> None:
        super().showEvent(event)
        self.upcoming_events.ensure_header_controls_visible()
        self.visibility_changed.emit(True)

    def hideEvent(
        self,
        event: QHideEvent,
    ) -> None:
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def show_from_tray(self) -> None:
        self.show()
        self.upcoming_events.ensure_header_controls_visible()
        self.raise_()
        self.activateWindow()

    def toggle_visibility(self) -> None:
        if self.isVisible():
            self.hide()
        else:
            self.show_from_tray()

    # ================================================================
    # UI
    # ================================================================

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        self.outer_container = QWidget()
        self.outer_container.setObjectName("outerContainer")
        self.outer_container.setStyleSheet(
            OUTER_CONTAINER_STYLE
        )

        outer_layout = QHBoxLayout(
            self.outer_container
        )
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.month_calendar = MonthCalendar()
        self.upcoming_events = UpcomingEventsPanel(
            days_ahead=self.upcoming_days
        )

        outer_layout.addWidget(
            self.month_calendar,
            1,
        )
        outer_layout.addWidget(
            self.upcoming_events,
            1,
        )

        main_layout.addWidget(
            self.outer_container
        )

    # ================================================================
    # SIGNALS
    # ================================================================

    def _connect_signals(self) -> None:
        self.controller.events_updated.connect(
            self._display_events
        )
        self.controller.error.connect(
            self._handle_calendar_error
        )

        self.upcoming_events.open_google_calendar_requested.connect(
            self._open_google_calendar
        )
        self.upcoming_events.refresh_requested.connect(
            self._refresh_now
        )
        self.upcoming_events.lock_position_requested.connect(
            self._change_position_lock
        )
        self.upcoming_events.upcoming_requested.connect(
            self._show_upcoming_mode
        )
        self.upcoming_events.close_requested.connect(
            self.hide
        )

        self.month_calendar.date_selected.connect(
            self._show_selected_date
        )
        self.month_calendar.month_changed.connect(
            self._month_changed
        )

    # ================================================================
    # TIMER
    # ================================================================

    def _setup_timer(self) -> None:
        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.controller.refresh
        )
        self.timer.start(
            self.REFRESH_INTERVAL_MS
        )

        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(
            self._update_sync_status
        )
        self.status_timer.start(30_000)

    def _update_sync_status(self) -> None:
        if self.last_successful_update is None:
            return

        age_text = self._age_text(
            self.last_successful_update
        )

        if self.sync_failed:
            self.upcoming_events.set_sync_status(
                f"• Showing saved events · Updated {age_text}",
                warning=True,
            )
        else:
            self.upcoming_events.set_sync_status(
                f"• Updated {age_text}"
            )

    # ================================================================
    # DISPLAY
    # ================================================================

    @Slot(list)
    def _display_events(
        self,
        events: list[CalendarEvent],
    ) -> None:
        self.month_calendar.set_events(events)
        self.upcoming_events.set_events(events)

        self.cache.save(events)

        self.last_successful_update = (
            datetime.now().astimezone()
        )
        self.sync_failed = False

        self._update_sync_status()

        self._install_mouse_tracking(
            self.outer_container
        )

    # ================================================================
    # DATE SELECTION
    # ================================================================

    @Slot(object)
    def _show_selected_date(
        self,
        selected_date: date,
    ) -> None:
        self.upcoming_events.show_date(
            selected_date
        )

    @Slot(object)
    def _month_changed(
        self,
        _month: date,
    ) -> None:
        self._show_upcoming_mode()

    @Slot()
    def _show_upcoming_mode(self) -> None:
        self.month_calendar.clear_selection()
        self.upcoming_events.show_upcoming()

    # ================================================================
    # ERROR
    # ================================================================

    @Slot(str)
    def _handle_calendar_error(
        self,
        message: str,
    ) -> None:
        print(
            "Google Calendar error:",
            message,
        )

        self.sync_failed = True

        if self.last_successful_update:
            self._update_sync_status()
        else:
            self.upcoming_events.set_sync_status(
                "• Couldn't connect to Google Calendar",
                warning=True,
            )

    # ================================================================
    # GOOGLE CALENDAR
    # ================================================================

    @Slot()
    def _open_google_calendar(self) -> None:
        QDesktopServices.openUrl(
            QUrl(
                "https://calendar.google.com/calendar/u/0/r"
            )
        )

    # ================================================================
    # SETTINGS
    # ================================================================

    @Slot()
    def open_settings(self) -> None:
        dialog = SettingsDialog(
            self.upcoming_days,
            self.preferred_browser,
            self if self.isVisible() else None,
        )

        if dialog.exec() != QDialog.Accepted:
            return

        new_days = dialog.upcoming_days()
        new_browser = dialog.browser()

        days_changed = (
            new_days != self.upcoming_days
        )
        browser_changed = (
            new_browser != self.preferred_browser
        )

        if not days_changed and not browser_changed:
            return

        if days_changed:
            self.upcoming_days = new_days
            self.settings.set_upcoming_days(
                new_days
            )

            self.upcoming_events.set_days_ahead(
                new_days
            )
            self._show_upcoming_mode()

        if browser_changed:
            self.preferred_browser = new_browser
            self.settings.set_browser(
                new_browser
            )

        self.settings.sync()

    # ================================================================
    # POSITION / LOCK
    # ================================================================

    @Slot()
    def _reset_position(self) -> None:
        self.position_manager.move_to_default_screen()

    @Slot(bool)
    def _change_position_lock(
        self,
        locked: bool,
    ) -> None:
        self.set_position_locked(locked)

    # ================================================================
    # REFRESH
    # ================================================================

    @Slot()
    def _refresh_now(self) -> None:
        self.upcoming_events.set_sync_status(
            "Refreshing..."
        )
        self.controller.refresh()

    # ================================================================
    # STATUS HELPERS
    # ================================================================

    def _saved_status_text(
        self,
        updated_at: datetime,
    ) -> str:
        return (
            "Showing saved events · Updated "
            + self._age_text(updated_at)
        )

    def _age_text(
        self,
        updated_at: datetime,
    ) -> str:
        now = datetime.now().astimezone()
        updated_at = updated_at.astimezone()

        seconds = max(
            0,
            (now - updated_at).total_seconds(),
        )
        minutes = int(seconds // 60)

        if minutes == 0:
            return "just now"

        if minutes == 1:
            return "1 min ago"

        if minutes < 60:
            return f"{minutes} min ago"

        hours = minutes // 60

        if hours == 1:
            return "1 hour ago"

        return f"{hours} hours ago"
