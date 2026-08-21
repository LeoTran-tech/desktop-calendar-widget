from datetime import datetime

from PySide6.QtCore import QDate, QTime
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
    QTimeEdit,
)

from models.calendar_event import CalendarEvent


class CreateItemDialog(QDialog):

    def __init__(self, item_type="event", parent=None):
        super().__init__(parent)

        self.item_type = item_type

        self.setWindowTitle(
            "New Task"
            if item_type == "task"
            else "New Event"
        )

        self.resize(400, 300)

        layout = QFormLayout(self)

        self.title_input = QLineEdit()

        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())

        self.start_time = QTimeEdit()
        self.start_time.setTime(QTime.currentTime())

        self.end_time = QTimeEdit()
        self.end_time.setTime(
            QTime.currentTime().addSecs(3600)
        )

        self.all_day = QCheckBox("All day")

        self.location_input = QLineEdit()

        self.description_input = QTextEdit()

        layout.addRow("Title", self.title_input)
        layout.addRow("Date", self.date_input)

        if item_type == "event":
            layout.addRow("", self.all_day)
            layout.addRow("Start", self.start_time)
            layout.addRow("End", self.end_time)
            layout.addRow("Location", self.location_input)

        layout.addRow(
            "Description",
            self.description_input,
        )

        buttons = QDialogButtonBox(
            QDialogButtonBox.Save
            | QDialogButtonBox.Cancel
        )

        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addRow(buttons)

        self.all_day.toggled.connect(
            self._all_day_changed
        )

    def _all_day_changed(self, checked):
        self.start_time.setEnabled(not checked)
        self.end_time.setEnabled(not checked)

    def build_event(self):
        title = self.title_input.text().strip()

        qdate = self.date_input.date()

        python_date = qdate.toPython()

        if self.item_type == "task":
            return CalendarEvent(
                summary=title,
                start=python_date,
                description=self.description_input.toPlainText(),
                item_type="task",
            )

        if self.all_day.isChecked():
            start = python_date
            end = None

        else:
            start = datetime.combine(
                python_date,
                self.start_time.time().toPython(),
            )

            end = datetime.combine(
                python_date,
                self.end_time.time().toPython(),
            )

        return CalendarEvent(
            summary=title,
            start=start,
            end=end,
            location=self.location_input.text(),
            description=self.description_input.toPlainText(),
            item_type="event",
        )