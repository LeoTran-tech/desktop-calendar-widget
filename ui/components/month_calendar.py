import calendar
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QGridLayout, QLabel, QVBoxLayout, QWidget

from models.calendar_event import CalendarEvent
from ui.styles import (
    DAY_STYLE,
    EVENT_DAY_STYLE,
    TITLE_STYLE,
    TODAY_STYLE,
    TRANSPARENT_PANEL_STYLE,
    WEEKDAY_STYLE,
)


class MonthCalendar(QWidget):
    """Owns only the month-grid UI and event markers."""

    WEEKDAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._shown_year: int | None = None
        self._shown_month: int | None = None
        self._day_labels: dict[date, QLabel] = {}

        self.setStyleSheet(TRANSPARENT_PANEL_STYLE)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(10)

        self.title = QLabel()
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setFont(QFont("Segoe UI", 18, QFont.DemiBold))
        self.title.setStyleSheet(TITLE_STYLE)
        self.layout.addWidget(self.title)

        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(4)
        self.layout.addLayout(self.calendar_grid)
        self.layout.addStretch()

        self.show_month(date.today())

    def show_month(self, target_date: date) -> None:
        if (
            self._shown_year == target_date.year
            and self._shown_month == target_date.month
        ):
            return

        self._shown_year = target_date.year
        self._shown_month = target_date.month
        self.title.setText(target_date.strftime("%B %Y").upper())
        self._rebuild_grid(target_date)

    def set_events(self, events: list[CalendarEvent]) -> None:
        today = date.today()
        self.show_month(today)

        event_dates = {
            event.event_date
            for event in events
            if (
                event.event_date.year == self._shown_year
                and event.event_date.month == self._shown_month
            )
        }

        for day_date, label in self._day_labels.items():
            if day_date == today:
                label.setStyleSheet(TODAY_STYLE)
                label.setText(str(day_date.day))
            elif day_date in event_dates:
                label.setStyleSheet(EVENT_DAY_STYLE)
                label.setText(f"{day_date.day} •")
            else:
                label.setStyleSheet(DAY_STYLE)
                label.setText(str(day_date.day))

    def _rebuild_grid(self, target_date: date) -> None:
        self._clear_grid()
        self._day_labels.clear()

        for column, day_name in enumerate(self.WEEKDAYS):
            label = QLabel(day_name)
            label.setAlignment(Qt.AlignCenter)
            label.setMinimumHeight(25)
            label.setStyleSheet(WEEKDAY_STYLE)
            self.calendar_grid.addWidget(label, 0, column)

        month_data = calendar.monthcalendar(target_date.year, target_date.month)

        for row, week in enumerate(month_data, start=1):
            for column, day_number in enumerate(week):
                label = QLabel()
                label.setAlignment(Qt.AlignCenter)
                label.setMinimumSize(30, 30)

                if day_number == 0:
                    label.setStyleSheet("background: transparent;")
                else:
                    day_date = date(
                        target_date.year,
                        target_date.month,
                        day_number,
                    )
                    label.setText(str(day_number))
                    label.setStyleSheet(
                        TODAY_STYLE if day_date == date.today() else DAY_STYLE
                    )
                    self._day_labels[day_date] = label

                self.calendar_grid.addWidget(label, row, column)

        for column in range(7):
            self.calendar_grid.setColumnStretch(column, 1)

    def _clear_grid(self) -> None:
        while self.calendar_grid.count():
            item = self.calendar_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
