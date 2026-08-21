from datetime import datetime

from PySide6.QtCore import Qt, QTimer, Slot, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QWidget,
)

from services.event_cache import EventCache

from controllers.calendar_controller import CalendarController
from models.calendar_event import CalendarEvent
from services.combined_calendar import CombinedCalendarService
from ui.behaviors.frameless_window import FramelessWindowBehavior
from ui.components.month_calendar import MonthCalendar
from ui.components.upcoming_events import UpcomingEventsPanel
from ui.styles import OUTER_CONTAINER_STYLE


class CalendarWidget(
    FramelessWindowBehavior,
    QWidget,
):
    """Top-level desktop calendar window."""

    REFRESH_INTERVAL_MS = 60_000

    def __init__(self) -> None:
        super().__init__()

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
        self._load_cached_events()

        self.controller.refresh()

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
            time_text = (
                self.cache_updated_at
                .astimezone()
                .strftime("%H:%M")
            )

            self.upcoming_events.set_sync_status(
                f"Showing saved events · Last updated {time_text}"
            )

    # ================================================================
    # WINDOW
    # ================================================================

    def _setup_window(self) -> None:

        self.setWindowTitle(
            "Desktop Calendar"
        )

        self.setWindowFlags(
            Qt.Window
            | Qt.FramelessWindowHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowSystemMenuHint
        )

        self.setAttribute(
            Qt.WA_TranslucentBackground
        )

        self.resize(850, 320)

        self.setMinimumSize(
            650,
            300,
        )

        self.setMouseTracking(True)

        self._reset_position()

    # ================================================================
    # UI
    # ================================================================

    def _setup_ui(self) -> None:

        main_layout = QHBoxLayout(self)

        main_layout.setContentsMargins(
            8,
            8,
            8,
            8,
        )

        main_layout.setSpacing(0)

        self.outer_container = QWidget()

        self.outer_container.setObjectName(
            "outerContainer"
        )

        self.outer_container.setStyleSheet(
            OUTER_CONTAINER_STYLE
        )

        outer_layout = QHBoxLayout(
            self.outer_container
        )

        outer_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        outer_layout.setSpacing(0)

        self.month_calendar = MonthCalendar()

        self.upcoming_events = UpcomingEventsPanel(
            days_ahead=self.service.days_ahead
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

    # ================================================================
    # TIMER
    # ================================================================

    def _setup_timer(self) -> None:

        # Sync Google mỗi phút
        self.timer = QTimer(self)
        self.timer.timeout.connect(
            self.controller.refresh
        )
        self.timer.start(
            self.REFRESH_INTERVAL_MS
        )

        # Chỉ update chữ status
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(
            self._update_sync_status
        )
        self.status_timer.start(30_000)

    def _update_sync_status(self) -> None:

        if self.last_successful_update is None:
            return

        now = datetime.now().astimezone()

        seconds = (
            now - self.last_successful_update
        ).total_seconds()

        minutes = max(
            0,
            int(seconds // 60),
        )

        if minutes == 0:
            age_text = "just now"
        elif minutes == 1:
            age_text = "1 min ago"
        elif minutes < 60:
            age_text = f"{minutes} min ago"
        else:
            hours = minutes // 60

            if hours == 1:
                age_text = "1 hour ago"
            else:
                age_text = f"{hours} hours ago"

        if self.sync_failed:

            self.upcoming_events.set_sync_status(
                f"⚠ Showing saved events · Updated {age_text}",
                warning=True,
            )

        else:

            self.upcoming_events.set_sync_status(
                f"✓ Updated {age_text}"
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
                "⚠ Couldn't connect to Google Calendar",
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
    # RESET POSITION
    # ================================================================

    @Slot()
    def _reset_position(self) -> None:

        screen = (
            QApplication
            .primaryScreen()
            .availableGeometry()
        )

        self.move(
            screen.right()
            - self.width()
            - 20,

            screen.top()
            + 20,
        )

    # ================================================================
    # LOCK POSITION
    # ================================================================

    @Slot(bool)
    def _change_position_lock(
        self,
        locked: bool,
    ) -> None:

        self.set_position_locked(
            locked
        )

    @Slot()
    def _refresh_now(self) -> None:
        self.upcoming_events.set_sync_status(
            "Refreshing..."
        )

        self.controller.refresh()