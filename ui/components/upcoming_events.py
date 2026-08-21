from html import escape
from datetime import date, timedelta

from PySide6.QtCore import Qt, Signal, QPoint
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QToolButton,
)

from models.calendar_event import CalendarEvent
from ui.styles import (
    EMPTY_STYLE,
    EVENT_CARD_STYLE,
    SCROLL_AREA_STYLE,
    TRANSPARENT_PANEL_STYLE,
    UPCOMING_TITLE_STYLE,
)


class HoverToolButton(QToolButton):
    hover_entered = Signal()
    hover_left = Signal()

    def enterEvent(self, event):
        self.hover_entered.emit()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.hover_left.emit()
        super().leaveEvent(event)


class UpcomingEventsPanel(QWidget):

    open_google_calendar_requested = Signal()
    lock_position_requested = Signal(bool)
    refresh_requested = Signal()

    def __init__(
        self,
        days_ahead: int = 14,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.days_ahead = days_ahead
        self.position_locked = True

        self.setStyleSheet(TRANSPARENT_PANEL_STYLE)

        # ============================================================
        # MAIN LAYOUT
        # ============================================================

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)

        # ============================================================
        # TITLE BAR
        # ============================================================

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(7)

        self.title = QLabel(self._title_text())

        self.title.setFont(
            QFont("Segoe UI", 16, QFont.DemiBold)
        )

        self.title.setStyleSheet(
            UPCOMING_TITLE_STYLE
        )

        title_layout.addWidget(self.title)
        title_layout.addStretch()

        # ============================================================
        # BUTTON STYLE
        # ============================================================

        button_style = """
        QToolButton {
            color: white;
            background-color: rgba(255,255,255,22);
            border: none;
            border-radius: 20px;

            font-family: "Segoe UI";
            font-size: 21px;
            font-weight: 600;
        }

        QToolButton:hover {
            background-color: rgba(255,255,255,42);
            color: #8ab4f8;
        }

        QToolButton:pressed {
            background-color: rgba(255,255,255,55);
        }
        """

        # ============================================================
        # RESET POSITION
        # ============================================================

        # REFRESH
        self.refresh_button = HoverToolButton()
        self.refresh_button.setText("↻")
        self.refresh_button.setFixedSize(40, 40)
        self.refresh_button.setCursor(Qt.PointingHandCursor)
        self.refresh_button.setStyleSheet(button_style)
        self.refresh_button.setProperty("interactive", True)

        self.refresh_button.clicked.connect(
            self.refresh_requested.emit
        )

        # ============================================================
        # LOCK / UNLOCK
        # ============================================================

        self.lock_button = HoverToolButton()
        self.lock_button.setText("🔒")
        self.lock_button.setFixedSize(40, 40)
        self.lock_button.setCursor(Qt.PointingHandCursor)
        self.lock_button.setStyleSheet(button_style)
        self.lock_button.setProperty("interactive", True)

        self.lock_button.clicked.connect(
            self._toggle_position_lock
        )

        # ============================================================
        # OPEN GOOGLE CALENDAR
        # ============================================================

        self.open_button = HoverToolButton()
        self.open_button.setText("↗")
        self.open_button.setFixedSize(40, 40)
        self.open_button.setCursor(Qt.PointingHandCursor)
        self.open_button.setStyleSheet(button_style)
        self.open_button.setProperty("interactive", True)

        self.open_button.clicked.connect(
            self.open_google_calendar_requested.emit
        )

        # ============================================================
        # ADD BUTTONS
        # ============================================================

        title_layout.addWidget(self.refresh_button)
        title_layout.addWidget(self.lock_button)
        title_layout.addWidget(self.open_button)

        layout.addLayout(title_layout)

        # ============================================================
        # CUSTOM TOOLTIP
        # ============================================================

        self.control_tooltip = QLabel("", self)

        self.control_tooltip.setStyleSheet("""
        QLabel {
            background-color: #353328;
            color: #FFFFFF;

            border: 1px solid rgba(255,255,255,35);
            border-radius: 7px;

            padding: 7px 11px;

            font-family: "Segoe UI";
            font-size: 13px;
            font-weight: 500;
        }
        """)

        self.control_tooltip.setAlignment(Qt.AlignCenter)

        self.control_tooltip.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )

        self.control_tooltip.hide()

        # Refresh tooltip
        self.refresh_button.hover_entered.connect(
            lambda: self._show_tooltip(
                self.refresh_button,
                "Refresh now",
            )
        )

        self.refresh_button.hover_left.connect(
            self._hide_tooltip
        )

        # Lock tooltip
        self.lock_button.hover_entered.connect(
            self._show_lock_tooltip
        )

        self.lock_button.hover_left.connect(
            self._hide_tooltip
        )

        # Google Calendar tooltip
        self.open_button.hover_entered.connect(
            lambda: self._show_tooltip(
                self.open_button,
                "Open Google Calendar",
            )
        )

        self.open_button.hover_left.connect(
            self._hide_tooltip
        )

        # ============================================================
        # SCROLL AREA
        # ============================================================

        self.scroll = QScrollArea()

        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.NoFrame)
        self.scroll.setStyleSheet(SCROLL_AREA_STYLE)

        self.content = QWidget()
        self.content.setStyleSheet(
            TRANSPARENT_PANEL_STYLE
        )

        self.events_layout = QVBoxLayout(self.content)

        self.events_layout.setContentsMargins(
            0,
            0,
            5,
            0,
        )

        self.events_layout.setSpacing(6)

        self.scroll.setWidget(self.content)

        layout.addWidget(self.scroll)

        self.sync_status = QLabel("")
        self.sync_status.setStyleSheet("""
        QLabel {
            color: #B8B8B8;
            background: transparent;
            border: none;

            font-family: "Segoe UI";
            font-size: 12px;
            font-weight: 500;

            padding: 4px 3px;
        }
        """)

        layout.addWidget(self.sync_status)

    def set_sync_status(
        self,
        text: str,
        warning: bool = False,
    ) -> None:

        color = "#D6B36A" if warning else "#B8B8B8"

        self.sync_status.setText(text)

        self.sync_status.setStyleSheet(f"""
        QLabel {{
            color: {color};
            background: transparent;
            border: none;

            font-family: "Segoe UI";
            font-size: 12px;
            font-weight: 500;

            padding: 4px 3px;
        }}
        """)

    # ================================================================
    # POSITION LOCK
    # ================================================================

    def _toggle_position_lock(self) -> None:

        self.position_locked = not self.position_locked

        if self.position_locked:
            self.lock_button.setText("🔒")
        else:
            self.lock_button.setText("🔓")

        self.lock_position_requested.emit(
            self.position_locked
        )

    # ================================================================
    # TOOLTIP
    # ================================================================

    def _show_lock_tooltip(self) -> None:

        text = (
            "Unlock position"
            if self.position_locked
            else "Lock position"
        )

        self._show_tooltip(
            self.lock_button,
            text,
        )

    def _show_tooltip(
        self,
        button: QToolButton,
        text: str,
    ) -> None:

        self.control_tooltip.setText(text)
        self.control_tooltip.adjustSize()

        button_pos = button.mapTo(
            self,
            QPoint(0, 0),
        )

        tooltip_width = (
            self.control_tooltip.sizeHint().width()
        )

        tooltip_height = (
            self.control_tooltip.sizeHint().height()
        )

        x = (
            button_pos.x()
            + button.width()
            - tooltip_width
        )

        y = (
            button_pos.y()
            + button.height()
            + 6
        )

        # Không cho tooltip vượt mép trái/phải.
        x = max(0, x)

        if x + tooltip_width > self.width():
            x = self.width() - tooltip_width

        self.control_tooltip.resize(
            tooltip_width,
            tooltip_height,
        )

        self.control_tooltip.move(x, y)
        self.control_tooltip.raise_()
        self.control_tooltip.show()

    def _hide_tooltip(self) -> None:
        self.control_tooltip.hide()

    # ================================================================
    # EVENTS
    # ================================================================

    def set_events(
        self,
        events: list[CalendarEvent],
    ) -> None:

        self._clear_events()

        today = date.today()

        end_date = today + timedelta(
            days=self.days_ahead
        )

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
                f"No events in the next "
                f"{self.days_ahead} days"
            )

            empty.setStyleSheet(EMPTY_STYLE)

            self.events_layout.addWidget(empty)
            self.events_layout.addStretch()

            return

        for event in upcoming:

            self.events_layout.addWidget(
                self._create_event_card(event)
            )

        self.events_layout.addStretch()

    # ================================================================
    # EVENT CARD
    # ================================================================

    def _create_event_card(
        self,
        event: CalendarEvent,
    ) -> QLabel:

        date_text = (
            event.event_date
            .strftime("%a, %d %b")
            .upper()
        )

        lines = [
            (
                f'<span style="font-size:14px; font-weight:600;">'
                f'{escape(date_text)}'
                f'</span>'
            ),
            (
                f'<span style="font-size:13px; font-weight:400;">'
                f'{escape(event.time_range_text)}'
                f'</span>'
                f' &nbsp;&nbsp; '
                f'<span style="font-size:14px; font-weight:600;">'
                f'{escape(event.summary)}'
                f'</span>'
            ),
        ]

        if event.location:

            location = event.location

            if not location.startswith("http"):
                lines.append(
                    f"📍 {escape(location)}"
                )

        if event.url:

            display_url = event.url

            if len(display_url) > 48:
                display_url = (
                    display_url[:45] + "..."
                )

            lines.append(
                f'🔗 <a href="{escape(event.url)}" '
                f'style="color:#8ab4f8;'
                f'text-decoration:none;">'
                f'{escape(display_url)}</a>'
            )

        if event.description:

            description = event.description

            if event.url:
                description = description.replace(
                    event.url,
                    "",
                )

            description = description.strip()

            if description:
                lines.append(
                    f"📝 {escape(description)}"
                )

        if event.reminders:

            lines.append(
                "🔔 "
                + escape(
                    ", ".join(event.reminders)
                )
            )

        if event.organizer:

            lines.append(
                f"👤 {escape(event.organizer)}"
            )

        if event.attendees:

            lines.append(
                "👥 "
                + escape(
                    ", ".join(event.attendees)
                )
            )

        label = QLabel(
            "<br>".join(lines)
        )

        label.setWordWrap(True)
        label.setStyleSheet(EVENT_CARD_STYLE)

        label.setTextFormat(Qt.RichText)

        label.setTextInteractionFlags(
            Qt.TextBrowserInteraction
        )

        label.setOpenExternalLinks(True)

        label.setProperty(
            "interactive",
            True,
        )

        label.setProperty(
            "event_id",
            event.event_id or "",
        )

        return label

    # ================================================================
    # CLEAR
    # ================================================================

    def _clear_events(self) -> None:

        while self.events_layout.count():

            item = self.events_layout.takeAt(0)

            widget = item.widget()

            if widget:
                widget.deleteLater()

    # ================================================================
    # TITLE
    # ================================================================

    def _title_text(self) -> str:

        if self.days_ahead == 14:
            return "NEXT 2 WEEKS"

        return f"NEXT {self.days_ahead} DAYS"