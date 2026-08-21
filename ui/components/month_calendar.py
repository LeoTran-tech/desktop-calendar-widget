import calendar
from datetime import date

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QMouseEvent, QWheelEvent
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from models.calendar_event import CalendarEvent
from ui.styles import (
    DAY_STYLE,
    EVENT_DAY_STYLE,
    SELECTED_DAY_STYLE,
    SELECTED_TODAY_STYLE,
    TITLE_STYLE,
    TODAY_STYLE,
    TRANSPARENT_PANEL_STYLE,
    WEEKDAY_STYLE,
)


class DayLabel(QLabel):
    clicked = Signal(object)

    def __init__(
        self,
        day_date: date,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.day_date = day_date
        self.setCursor(
            Qt.PointingHandCursor
        )
        self.setProperty(
            "interactive",
            True,
        )

    def mousePressEvent(
        self,
        event: QMouseEvent,
    ) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(
                self.day_date
            )
            event.accept()
            return

        super().mousePressEvent(event)


class MonthCalendar(QWidget):
    """Compact month grid with limited wheel navigation and date selection."""

    date_selected = Signal(object)
    month_changed = Signal(object)

    WEEKDAYS = (
        "MON",
        "TUE",
        "WED",
        "THU",
        "FRI",
        "SAT",
        "SUN",
    )

    MONTHS_BACK = 1
    MONTHS_FORWARD = 2

    def __init__(
        self,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        today = date.today()

        self._anchor_month = date(
            today.year,
            today.month,
            1,
        )
        self._shown_year: int | None = None
        self._shown_month: int | None = None
        self._day_labels: dict[
            date,
            DayLabel,
        ] = {}
        self._events: list[
            CalendarEvent
        ] = []
        self._selected_date: date | None = None

        self.setStyleSheet(
            TRANSPARENT_PANEL_STYLE
        )

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )
        self.layout.setSpacing(10)

        self.title = QLabel()
        self.title.setAlignment(
            Qt.AlignCenter
        )
        self.title.setFont(
            QFont(
                "Segoe UI",
                18,
                QFont.DemiBold,
            )
        )
        self.title.setStyleSheet(
            TITLE_STYLE
        )
        self.layout.addWidget(
            self.title
        )

        self.calendar_grid = QGridLayout()
        self.calendar_grid.setSpacing(4)
        self.layout.addLayout(
            self.calendar_grid
        )
        self.layout.addStretch()

        self.show_month(today)

    def show_month(
        self,
        target_date: date,
    ) -> None:
        if (
            self._shown_year
            == target_date.year
            and self._shown_month
            == target_date.month
        ):
            self._apply_event_markers()
            return

        self._shown_year = target_date.year
        self._shown_month = target_date.month

        self.title.setText(
            target_date
            .strftime("%B %Y")
            .upper()
        )

        self._rebuild_grid(
            target_date
        )
        self._apply_event_markers()

    def set_events(
        self,
        events: list[CalendarEvent],
    ) -> None:
        self._events = list(events)
        self._apply_event_markers()

    def clear_selection(self) -> None:
        if self._selected_date is None:
            return

        self._selected_date = None
        self._apply_event_markers()

    def wheelEvent(
        self,
        event: QWheelEvent,
    ) -> None:
        delta = event.angleDelta().y()

        if delta == 0:
            event.ignore()
            return

        changed = self._change_month(
            -1 if delta > 0 else 1
        )

        if changed:
            event.accept()
        else:
            event.ignore()

    def _change_month(
        self,
        delta: int,
    ) -> bool:
        if (
            self._shown_year is None
            or self._shown_month is None
        ):
            return False

        current_index = (
            self._shown_year * 12
            + self._shown_month
            - 1
        )
        anchor_index = (
            self._anchor_month.year * 12
            + self._anchor_month.month
            - 1
        )

        target_index = current_index + delta
        minimum = (
            anchor_index
            - self.MONTHS_BACK
        )
        maximum = (
            anchor_index
            + self.MONTHS_FORWARD
        )

        target_index = max(
            minimum,
            min(maximum, target_index),
        )

        if target_index == current_index:
            return False

        year, month_zero = divmod(
            target_index,
            12,
        )
        target_month = date(
            year,
            month_zero + 1,
            1,
        )

        self.show_month(
            target_month
        )
        self.month_changed.emit(
            target_month
        )
        return True

    def _select_date(
        self,
        selected_date: date,
    ) -> None:
        self._selected_date = selected_date
        self._apply_event_markers()
        self.date_selected.emit(
            selected_date
        )

    def _apply_event_markers(self) -> None:
        if (
            self._shown_year is None
            or self._shown_month is None
        ):
            return

        today = date.today()

        event_dates = {
            event.event_date
            for event in self._events
            if (
                event.event_date.year
                == self._shown_year
                and event.event_date.month
                == self._shown_month
            )
        }

        for day_date, label in (
            self._day_labels.items()
        ):
            has_event = (
                day_date in event_dates
            )

            label.setText(
                f"{day_date.day} •"
                if has_event
                else str(day_date.day)
            )

            if day_date == self._selected_date:
                label.setStyleSheet(
                    SELECTED_TODAY_STYLE
                    if day_date == today
                    else SELECTED_DAY_STYLE
                )
            elif day_date == today:
                label.setStyleSheet(
                    TODAY_STYLE
                )
            elif has_event:
                label.setStyleSheet(
                    EVENT_DAY_STYLE
                )
            else:
                label.setStyleSheet(
                    DAY_STYLE
                )

    def _rebuild_grid(
        self,
        target_date: date,
    ) -> None:
        self._clear_grid()
        self._day_labels.clear()

        for column, day_name in enumerate(
            self.WEEKDAYS
        ):
            label = QLabel(day_name)
            label.setAlignment(
                Qt.AlignCenter
            )
            label.setMinimumHeight(27)
            label.setStyleSheet(
                WEEKDAY_STYLE
            )
            self.calendar_grid.addWidget(
                label,
                0,
                column,
            )

        month_data = calendar.monthcalendar(
            target_date.year,
            target_date.month,
        )

        for row, week in enumerate(
            month_data,
            start=1,
        ):
            for column, day_number in enumerate(
                week
            ):
                if day_number == 0:
                    label = QLabel()
                    label.setStyleSheet(
                        "background: transparent;"
                    )
                else:
                    day_date = date(
                        target_date.year,
                        target_date.month,
                        day_number,
                    )
                    label = DayLabel(
                        day_date
                    )
                    label.clicked.connect(
                        self._select_date
                    )
                    self._day_labels[
                        day_date
                    ] = label

                label.setAlignment(
                    Qt.AlignCenter
                )
                label.setMinimumSize(
                    30,
                    30,
                )

                self.calendar_grid.addWidget(
                    label,
                    row,
                    column,
                )

        for column in range(7):
            self.calendar_grid.setColumnStretch(
                column,
                1,
            )

    def _clear_grid(self) -> None:
        while self.calendar_grid.count():
            item = self.calendar_grid.takeAt(0)
            widget = item.widget()

            if widget:
                widget.deleteLater()
