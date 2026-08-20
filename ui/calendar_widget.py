import calendar
from datetime import datetime

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QLabel,
    QGridLayout
)
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QFont

from services.google_calendar import GoogleCalendarService
from ui.styles import (
    CONTAINER_STYLE,
    TITLE_STYLE,
    WEEKDAY_STYLE,
    DAY_STYLE,
    TODAY_STYLE,
    EVENT_DAY_STYLE,
    UPCOMING_TITLE_STYLE,
    EVENT_STYLE,
    EMPTY_STYLE,
)


class CalendarWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.service = GoogleCalendarService()
        self.events = []
        self.day_labels = {}

        self.resize_margin = 10
        self.resize_edges = None
        self.resize_start_geometry = None
        self.resize_start_mouse = None
        self.drag_position = None

        self._setup_window()
        self._setup_ui()
        self._setup_timer()

        self.refresh()

    def _setup_window(self):
        self.setWindowTitle("Desktop Calendar")
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.Tool
            | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.resize(420, 560)
        self.setMinimumSize(300, 350)
        self.setMouseTracking(True)

        screen = QApplication.primaryScreen().availableGeometry()
        self.move(
            screen.right() - self.width() - 20,
            screen.top() + 20
        )

    def _setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)

        self.container = QWidget()
        self.container.setObjectName("container")
        self.container.setStyleSheet(CONTAINER_STYLE)

        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        self.main_layout.addWidget(self.container)

        self._create_header()
        self._create_calendar()
        self._create_upcoming()

        self.install_mouse_tracking(self)

    def _setup_timer(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(300000)  # 5 phút

    def _create_header(self):
        self.title = QLabel(datetime.now().strftime("%B %Y").upper())
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 19, QFont.Bold))
        self.title.setStyleSheet(TITLE_STYLE)
        self.layout.addWidget(self.title)

    def _create_calendar(self):
        now = datetime.now()
        year, month, today = now.year, now.month, now.day

        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(4)

        weekdays = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]

        for col, day_name in enumerate(weekdays):
            label = QLabel(day_name)
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumHeight(25)
            label.setStyleSheet(WEEKDAY_STYLE)
            self.calendar_grid.addWidget(label, 0, col)

        month_data = calendar.monthcalendar(year, month)

        for row, week in enumerate(month_data):
            for col, day in enumerate(week):
                label = QLabel()
                label.setAlignment(Qt.AlignCenter)
                label.setMinimumSize(30, 30)

                if day == 0:
                    label.setText("")
                    label.setStyleSheet("background: transparent;")
                else:
                    label.setText(str(day))
                    label.setStyleSheet(
                        TODAY_STYLE if day == today else DAY_STYLE
                    )
                    self.day_labels[day] = label

                self.calendar_grid.addWidget(label, row + 1, col)

        for col in range(7):
            self.calendar_grid.setColumnStretch(col, 1)

        self.layout.addLayout(self.calendar_grid)

    def _create_upcoming(self):
        self.upcoming_title = QLabel("UPCOMING")
        self.upcoming_title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.upcoming_title.setStyleSheet(UPCOMING_TITLE_STYLE)
        self.layout.addWidget(self.upcoming_title)

        self.events_layout = QVBoxLayout()
        self.events_layout.setSpacing(5)

        self.layout.addLayout(self.events_layout)
        self.layout.addStretch()

    def refresh(self):
        try:
            self.events = self.service.get_events()
        except Exception as e:
            print("Google Calendar error:", e)
            self.events = []

        self._update_event_markers()
        self._update_upcoming_events()

    def _update_event_markers(self):
        now = datetime.now()
        event_days = {
            event["date"].day
            for event in self.events
            if event["date"].year == now.year
            and event["date"].month == now.month
        }

        for day, label in self.day_labels.items():
            if day == now.day:
                label.setStyleSheet(TODAY_STYLE)
                label.setText(str(day))
            elif day in event_days:
                label.setStyleSheet(EVENT_DAY_STYLE)
                label.setText(f"{day} •")
            else:
                label.setStyleSheet(DAY_STYLE)
                label.setText(str(day))

    def _update_upcoming_events(self):
        while self.events_layout.count():
            item = self.events_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        if not self.events:
            label = QLabel("No upcoming events")
            label.setStyleSheet(EMPTY_STYLE)
            self.events_layout.addWidget(label)
            self.install_mouse_tracking(label)
            return

        for event in self.events[:8]:
            date_text = event["date"].strftime("%d %b").upper()
            text = f'{date_text}  {event["time"]}   {event["summary"]}'

            label = QLabel(text)
            label.setWordWrap(True)
            label.setStyleSheet(EVENT_STYLE)

            self.events_layout.addWidget(label)
            self.install_mouse_tracking(label)

    def install_mouse_tracking(self, widget):
        widget.setMouseTracking(True)
        widget.installEventFilter(self)

        for child in widget.findChildren(QWidget):
            child.setMouseTracking(True)
            child.installEventFilter(self)

    def get_resize_edges(self, global_pos):
        local = self.mapFromGlobal(global_pos)

        x, y = local.x(), local.y()
        w, h = self.width(), self.height()
        m = self.resize_margin

        return (
            x <= m,
            x >= w - m,
            y <= m,
            y >= h - m,
        )

    def update_cursor(self, global_pos):
        left, right, top, bottom = self.get_resize_edges(global_pos)

        if (left and top) or (right and bottom):
            self.setCursor(Qt.SizeFDiagCursor)
        elif (right and top) or (left and bottom):
            self.setCursor(Qt.SizeBDiagCursor)
        elif left or right:
            self.setCursor(Qt.SizeHorCursor)
        elif top or bottom:
            self.setCursor(Qt.SizeVerCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseMove:
            global_pos = event.globalPosition().toPoint()

            if (
                event.buttons() & Qt.LeftButton
                and self.resize_edges
            ):
                self.perform_resize(global_pos)
                return True

            if (
                event.buttons() & Qt.LeftButton
                and self.drag_position is not None
            ):
                self.move(global_pos - self.drag_position)
                return True

            self.update_cursor(global_pos)

        elif event.type() == QEvent.MouseButtonPress:
            if event.button() == Qt.LeftButton:
                global_pos = event.globalPosition().toPoint()
                edges = self.get_resize_edges(global_pos)

                if any(edges):
                    self.resize_edges = edges
                    self.resize_start_geometry = self.geometry()
                    self.resize_start_mouse = global_pos
                    return True

                self.drag_position = (
                    global_pos - self.frameGeometry().topLeft()
                )
                return True

        elif event.type() == QEvent.MouseButtonRelease:
            if event.button() == Qt.LeftButton:
                self.resize_edges = None
                self.resize_start_geometry = None
                self.resize_start_mouse = None
                self.drag_position = None
                return True

        return super().eventFilter(obj, event)

    def perform_resize(self, global_pos):
        if self.resize_start_geometry is None:
            return

        left, right, top, bottom = self.resize_edges
        delta = global_pos - self.resize_start_mouse
        rect = self.resize_start_geometry

        x, y = rect.x(), rect.y()
        w, h = rect.width(), rect.height()

        min_w = self.minimumWidth()
        min_h = self.minimumHeight()

        if left:
            new_width = w - delta.x()
            if new_width >= min_w:
                x = rect.x() + delta.x()
                w = new_width

        if right:
            w = max(min_w, w + delta.x())

        if top:
            new_height = h - delta.y()
            if new_height >= min_h:
                y = rect.y() + delta.y()
                h = new_height

        if bottom:
            h = max(min_h, h + delta.y())

        self.setGeometry(x, y, w, h)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.RightButton:
            self.close()
