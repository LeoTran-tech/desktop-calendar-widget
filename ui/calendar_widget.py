from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget

from controllers.calendar_controller import CalendarController
from models.calendar_event import CalendarEvent
from services.combined_calendar import CombinedCalendarService
from ui.behaviors.frameless_window import FramelessWindowBehavior
from ui.components.month_calendar import MonthCalendar
from ui.components.upcoming_events import UpcomingEventsPanel
from ui.styles import OUTER_CONTAINER_STYLE


class CalendarWidget(FramelessWindowBehavior, QWidget):
    """Top-level window.

    Its job is intentionally small:
    - configure the window
    - compose child widgets
    - connect controller signals
    """

    REFRESH_INTERVAL_MS = 300_000

    def __init__(self) -> None:
        super().__init__()

        self.service = CombinedCalendarService()
        self.controller = CalendarController(self.service, self)

        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._setup_timer()
        self._init_frameless_behavior()

        self.controller.refresh()

    def _setup_window(self) -> None:
        self.setWindowTitle("Desktop Calendar")
        self.setWindowFlags(
            Qt.Window
            | Qt.FramelessWindowHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowSystemMenuHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(850, 320)
        self.setMinimumSize(650, 300)
        self.setMouseTracking(True)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.right() - self.width() - 20,
            screen.top() + 20,
        )

    def _setup_ui(self) -> None:
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(0)

        self.outer_container = QWidget()
        self.outer_container.setObjectName("outerContainer")
        self.outer_container.setStyleSheet(OUTER_CONTAINER_STYLE)

        outer_layout = QHBoxLayout(self.outer_container)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.month_calendar = MonthCalendar()
        self.upcoming_events = UpcomingEventsPanel(
            days_ahead=self.service.days_ahead
        )

        outer_layout.addWidget(self.month_calendar, 1)
        outer_layout.addWidget(self.upcoming_events, 1)
        main_layout.addWidget(self.outer_container)

    def _connect_signals(self) -> None:
        self.controller.events_updated.connect(self._display_events)
        self.controller.error.connect(self._handle_calendar_error)

    def _setup_timer(self) -> None:
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.controller.refresh)
        self.timer.start(self.REFRESH_INTERVAL_MS)

    @Slot(list)
    def _display_events(self, events: list[CalendarEvent]) -> None:
        self.month_calendar.set_events(events)
        self.upcoming_events.set_events(events)
        self._install_mouse_tracking(self.outer_container)

    @Slot(str)
    def _handle_calendar_error(self, message: str) -> None:
        print("Google Calendar error:", message)
        self.month_calendar.set_events([])
        self.upcoming_events.set_events([])
