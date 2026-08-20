from html import escape
from PySide6.QtCore import Qt
from datetime import date, timedelta

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout, QWidget

from models.calendar_event import CalendarEvent
from ui.styles import (
    EMPTY_STYLE,
    EVENT_CARD_STYLE,
    SCROLL_AREA_STYLE,
    TRANSPARENT_PANEL_STYLE,
    UPCOMING_TITLE_STYLE,
)


class UpcomingEventsPanel(QWidget):
    """Displays upcoming events and nothing else."""

    def __init__(
        self,
        days_ahead: int = 14,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.days_ahead = days_ahead
        self.setStyleSheet(TRANSPARENT_PANEL_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        self.title = QLabel(self._title_text())
        self.title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title.setStyleSheet(UPCOMING_TITLE_STYLE)
        layout.addWidget(self.title)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setStyleSheet(SCROLL_AREA_STYLE)

        self.content = QWidget()
        self.content.setStyleSheet(TRANSPARENT_PANEL_STYLE)

        self.events_layout = QVBoxLayout(self.content)
        self.events_layout.setContentsMargins(0, 0, 5, 0)
        self.events_layout.setSpacing(6)

        self.scroll.setWidget(self.content)
        layout.addWidget(self.scroll)

    def set_events(self, events: list[CalendarEvent]) -> None:
        self._clear_events()

        today = date.today()
        end_date = today + timedelta(days=self.days_ahead)

        upcoming = sorted(
            (
                event
                for event in events
                if today <= event.event_date < end_date
            ),
            key=lambda event: event.sort_key(),
        )

        if not upcoming:
            empty = QLabel(
                f"No events in the next {self.days_ahead} days"
            )
            empty.setStyleSheet(EMPTY_STYLE)
            self.events_layout.addWidget(empty)
            self.events_layout.addStretch()
            return

        for event in upcoming:
            self.events_layout.addWidget(self._create_event_card(event))

        self.events_layout.addStretch()

    def _create_event_card(self, event: CalendarEvent) -> QLabel:
        date_text = event.event_date.strftime("%a, %d %b").upper()
        if event.item_type == "task":
            type_text = "TASK"
        else:
            type_text = "EVENT"

        lines = [
            f'<span style="color:#8ab4f8;"><b>{type_text}</b></span>',
            f"<b>{escape(date_text)}</b>",
            f"{escape(event.time_range_text)} &nbsp;&nbsp;"
            f"<b>{escape(event.summary)}</b>",
        ]
        
        date_text = event.event_date.strftime("%a, %d %b").upper()

        lines = [
            f"<b>{escape(date_text)}</b>",
            f"{escape(event.time_range_text)} &nbsp;&nbsp; "
            f"<b>{escape(event.summary)}</b>",
        ]

        if event.location:
            location = event.location

            # Đừng hiện nguyên URL ở location
            if not location.startswith("http"):
                lines.append(f"📍 {escape(location)}")

        if event.url:
            display_url = event.url

            if len(display_url) > 48:
                display_url = display_url[:45] + "..."

            lines.append(
                f'🔗 <a href="{escape(event.url)}" '
                f'style="color:#8ab4f8;text-decoration:none;">'
                f'{escape(display_url)}</a>'
            )

        if event.description:
            description = event.description

            # Không lặp lại URL nếu description chứa link
            if event.url:
                description = description.replace(event.url, "")

            description = description.strip()

            if description:
                lines.append(f"📝 {escape(description)}")

        if event.reminders:
            lines.append(
                "🔔 " + escape(", ".join(event.reminders))
            )

        if event.organizer:
            lines.append(
                f"👤 {escape(event.organizer)}"
            )

        if event.attendees:
            lines.append(
                "👥 " + escape(", ".join(event.attendees))
            )

        label = QLabel("<br>".join(lines))

        label.setWordWrap(True)
        label.setStyleSheet(EVENT_CARD_STYLE)

        label.setTextFormat(Qt.RichText)
        label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        label.setOpenExternalLinks(True)

        label.setProperty("interactive", True)
        label.setProperty("event_id", event.event_id or "")

        return label

    def _clear_events(self) -> None:
        while self.events_layout.count():
            item = self.events_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def _title_text(self) -> str:
        if self.days_ahead == 14:
            return "NEXT 2 WEEKS"
        return f"NEXT {self.days_ahead} DAYS"
