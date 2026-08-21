from html import escape
from datetime import date
from urllib.parse import urlparse

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from models.calendar_event import CalendarEvent
from ui.icons import ICON_ACCENT, ICON_SECONDARY, make_icon


PRIMARY_TEXT = "#F5F5F5"
SECONDARY_TEXT = "#C9CDD2"
MUTED_TEXT = "#B9BEC5"


class EventCard(QFrame):
    """Compact calendar card with restrained monochrome metadata icons."""

    def __init__(
        self,
        event: CalendarEvent,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.setObjectName("eventCard")
        self.setProperty("interactive", True)
        self.setProperty("event_id", event.event_id or "")
        self.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Minimum,
        )
        self.setStyleSheet(
            """
            QFrame#eventCard {
                background-color: rgba(255, 255, 255, 18);
                border: 1px solid rgba(255, 255, 255, 8);
                border-radius: 9px;
            }
            QFrame#eventCard:hover {
                background-color: rgba(255, 255, 255, 25);
                border-color: rgba(138, 180, 248, 34);
            }
            QLabel {
                background: transparent;
                border: none;
                font-family: "Segoe UI";
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(3)

        date_text = (
            event.event_date
            .strftime("%a, %d %b")
            .upper()
        )
        date_row = QHBoxLayout()
        date_row.setContentsMargins(0, 0, 0, 0)
        date_row.setSpacing(6)

        date_label = self._label(
            date_text,
            color=PRIMARY_TEXT,
            size=12,
            weight=QFont.DemiBold,
        )
        date_row.addWidget(date_label, 0)

        relative_label = self._label(
            self._relative_date_text(event.event_date),
            color="#AEB4BC",
            size=10,
            weight=QFont.Normal,
        )
        date_row.addWidget(relative_label, 0)
        date_row.addStretch()

        layout.addLayout(date_row)

        main_row = QHBoxLayout()
        main_row.setContentsMargins(0, 0, 0, 0)
        main_row.setSpacing(9)

        time_label = self._label(
            event.time_range_text,
            color=SECONDARY_TEXT,
            size=11,
        )
        time_label.setMinimumWidth(78)
        main_row.addWidget(time_label, 0, Qt.AlignTop)

        title_label = self._label(
            event.summary,
            color=PRIMARY_TEXT,
            size=12,
            weight=QFont.DemiBold,
            wrap=True,
        )
        main_row.addWidget(title_label, 1)
        layout.addLayout(main_row)

        if event.location and not event.location.startswith("http"):
            self._add_meta_row(
                layout,
                "location",
                event.location,
            )

        if event.url:
            self._add_link_row(
                layout,
                event.url,
                self._compact_url(event.url),
            )

        if event.description:
            description = event.description
            if event.url:
                description = description.replace(event.url, "")
            description = description.strip()

            if description:
                self._add_meta_row(
                    layout,
                    "note",
                    description,
                )

        if event.reminders:
            self._add_meta_row(
                layout,
                "bell",
                ", ".join(event.reminders),
            )

        if event.organizer:
            self._add_meta_row(
                layout,
                "person",
                event.organizer,
            )

        if event.attendees:
            self._add_meta_row(
                layout,
                "people",
                ", ".join(event.attendees),
            )

        for child in self.findChildren(QWidget):
            child.setProperty("interactive", True)

    def _add_meta_row(
        self,
        parent_layout: QVBoxLayout,
        icon_name: str,
        text: str,
    ) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(7)

        icon = QLabel()
        icon.setFixedSize(16, 16)
        icon.setPixmap(
            make_icon(
                icon_name,
                ICON_SECONDARY,
                16,
                stroke_width=2.15,
            ).pixmap(16, 16)
        )
        row.addWidget(icon, 0, Qt.AlignTop)

        text_label = self._label(
            text,
            color=MUTED_TEXT,
            size=11,
            wrap=True,
        )
        row.addWidget(text_label, 1)
        parent_layout.addLayout(row)

    def _add_link_row(
        self,
        parent_layout: QVBoxLayout,
        url: str,
        display_url: str,
    ) -> None:
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(7)

        icon = QLabel()
        icon.setFixedSize(16, 16)
        icon.setPixmap(
            make_icon(
                "link",
                ICON_ACCENT,
                16,
                stroke_width=2.15,
            ).pixmap(16, 16)
        )
        row.addWidget(icon, 0, Qt.AlignVCenter)

        link = QLabel(
            f'<a href="{escape(url)}" '
            f'style="color:{ICON_ACCENT}; text-decoration:none;">'
            f'{escape(display_url)}</a>'
        )
        link.setFont(QFont("Segoe UI", 11))
        link.setTextFormat(Qt.RichText)
        link.setTextInteractionFlags(Qt.TextBrowserInteraction)
        link.setOpenExternalLinks(True)
        link.setWordWrap(False)
        link.setProperty("interactive", True)
        row.addWidget(link, 1)

        parent_layout.addLayout(row)


    @staticmethod
    def _relative_date_text(event_date: date) -> str:
        days = (event_date - date.today()).days

        if days == 0:
            return "· today"
        if days == 1:
            return "· tomorrow"
        if days > 1:
            return f"· in {days} days"
        if days == -1:
            return "· yesterday"
        return f"· {abs(days)} days ago"

    @staticmethod
    def _compact_url(url: str) -> str:
        """Show a useful one-line URL label instead of the full long URL."""
        try:
            parsed = urlparse(url)
            host = parsed.netloc.removeprefix("www.")
            path_parts = [part for part in parsed.path.split("/") if part]

            if host:
                if path_parts:
                    text = f"{host}/{path_parts[0]}/..."
                else:
                    text = host
            else:
                text = url
        except Exception:
            text = url

        if len(text) > 38:
            return text[:35] + "..."
        return text

    @staticmethod
    def _label(
        text: str,
        *,
        color: str,
        size: int,
        weight: int = QFont.Normal,
        wrap: bool = False,
    ) -> QLabel:
        label = QLabel(text)
        label.setWordWrap(wrap)
        label.setStyleSheet(
            f"color: {color}; background: transparent; border: none;"
        )
        label.setFont(
            QFont(
                "Segoe UI",
                size,
                weight,
            )
        )
        label.setProperty("interactive", True)
        return label
