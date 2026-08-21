from datetime import date, timedelta

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from models.calendar_event import CalendarEvent
from ui.components.event_card import EventCard
from ui.icons import ICON_ACCENT, ICON_DANGER, ICON_PRIMARY, make_icon
from ui.styles import (
    EMPTY_STYLE,
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


class IconToolButton(HoverToolButton):
    """Tool button with a monochrome icon that turns blue on hover."""

    def __init__(
        self,
        icon_name: str,
        icon_size: int = 22,
        hover_color: str = ICON_ACCENT,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._icon_name = icon_name
        self._icon_size = icon_size
        self._hover_color = hover_color
        self._active = False
        self.setIconSize(QSize(icon_size, icon_size))
        self._apply_icon()

    def set_icon_name(self, icon_name: str) -> None:
        self._icon_name = icon_name
        self._apply_icon()

    def set_active(self, active: bool) -> None:
        self._active = active
        self._apply_icon()

    def enterEvent(self, event):
        self.setIcon(
            make_icon(
                self._icon_name,
                self._hover_color,
                self._icon_size,
            )
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._apply_icon()
        super().leaveEvent(event)

    def _apply_icon(self) -> None:
        color = ICON_ACCENT if self._active else ICON_PRIMARY
        self.setIcon(
            make_icon(
                self._icon_name,
                color,
                self._icon_size,
            )
        )


class UpcomingEventsPanel(QWidget):
    open_google_calendar_requested = Signal()
    lock_position_requested = Signal(bool)
    refresh_requested = Signal()
    upcoming_requested = Signal()
    close_requested = Signal()

    def __init__(
        self,
        days_ahead: int = 7,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.days_ahead = days_ahead
        self.position_locked = True
        self._events: list[CalendarEvent] = []
        self._selected_date: date | None = None

        self.setStyleSheet(
            TRANSPARENT_PANEL_STYLE
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            20,
            20,
            20,
            20,
        )
        layout.setSpacing(10)

        # ============================================================
        # TITLE BAR
        # ============================================================

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        title_layout.setSpacing(7)

        self.back_button = IconToolButton(
            "back",
            icon_size=20,
        )
        self.back_button.setFixedSize(
            34,
            34,
        )
        self.back_button.setCursor(
            Qt.PointingHandCursor
        )
        self.back_button.setProperty(
            "interactive",
            True,
        )
        self.back_button.hide()

        self.title = QLabel(
            self._title_text()
        )
        self.title.setFont(
            QFont(
                "Segoe UI",
                16,
                QFont.DemiBold,
            )
        )
        self.title.setStyleSheet(
            UPCOMING_TITLE_STYLE
        )
        # Keep the header title visible while still allowing it to share
        # space with the fixed-size action buttons. Using Ignored here can
        # collapse labels such as "NEXT 30 DAYS" to zero width.
        self.title.setMinimumWidth(145)
        self.title.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Preferred,
        )

        title_layout.addWidget(
            self.back_button
        )
        title_layout.addWidget(
            self.title
        )
        title_layout.addStretch()

        button_style = """
        QToolButton {
            background-color: rgba(255,255,255,22);
            border: 1px solid rgba(255,255,255,8);
            border-radius: 20px;
        }

        QToolButton:hover {
            background-color: rgba(255,255,255,38);
            border-color: rgba(138,180,248,35);
        }

        QToolButton:pressed {
            background-color: rgba(255,255,255,52);
        }
        """

        close_button_style = """
        QToolButton {
            background-color: rgba(255,255,255,22);
            border: 1px solid rgba(255,255,255,8);
            border-radius: 20px;
        }

        QToolButton:hover {
            background-color: rgba(220,70,70,52);
            border-color: rgba(255,133,133,90);
        }

        QToolButton:pressed {
            background-color: rgba(220,70,70,78);
            border-color: rgba(255,133,133,120);
        }
        """

        compact_button_style = """
        QToolButton {
            background: transparent;
            border: none;
            border-radius: 17px;
        }

        QToolButton:hover {
            background-color: rgba(255,255,255,18);
        }
        """

        self.back_button.setStyleSheet(
            compact_button_style
        )

        self.refresh_button = IconToolButton(
            "refresh",
            icon_size=22,
        )
        self.refresh_button.setFixedSize(
            40,
            40,
        )
        self.refresh_button.setCursor(
            Qt.PointingHandCursor
        )
        self.refresh_button.setStyleSheet(
            button_style
        )
        self.refresh_button.setProperty(
            "interactive",
            True,
        )
        self.refresh_button.clicked.connect(
            self.refresh_requested.emit
        )

        self.lock_button = IconToolButton(
            "lock",
            icon_size=21,
        )
        self.lock_button.setFixedSize(
            40,
            40,
        )
        self.lock_button.setCursor(
            Qt.PointingHandCursor
        )
        self.lock_button.setStyleSheet(
            button_style
        )
        self.lock_button.setProperty(
            "interactive",
            True,
        )
        self.lock_button.clicked.connect(
            self._toggle_position_lock
        )

        self.open_button = IconToolButton(
            "external",
            icon_size=21,
        )
        self.open_button.setFixedSize(
            40,
            40,
        )
        self.open_button.setCursor(
            Qt.PointingHandCursor
        )
        self.open_button.setStyleSheet(
            button_style
        )
        self.open_button.setProperty(
            "interactive",
            True,
        )
        self.open_button.clicked.connect(
            self.open_google_calendar_requested.emit
        )

        self.close_button = IconToolButton(
            "close",
            icon_size=20,
            hover_color=ICON_DANGER,
        )
        self.close_button.setFixedSize(
            40,
            40,
        )
        self.close_button.setCursor(
            Qt.PointingHandCursor
        )
        self.close_button.setStyleSheet(
            close_button_style
        )
        self.close_button.setProperty(
            "interactive",
            True,
        )
        self.close_button.clicked.connect(
            self.close_requested.emit
        )

        title_layout.addWidget(
            self.refresh_button
        )
        title_layout.addWidget(
            self.lock_button
        )
        title_layout.addWidget(
            self.open_button
        )
        title_layout.addWidget(
            self.close_button
        )

        layout.addLayout(title_layout)

        # ============================================================
        # CUSTOM TOOLTIP
        # ============================================================

        self.control_tooltip = QLabel(
            "",
            self,
        )
        self.control_tooltip.setStyleSheet(
            """
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
            """
        )
        self.control_tooltip.setAlignment(
            Qt.AlignCenter
        )
        self.control_tooltip.setAttribute(
            Qt.WA_TransparentForMouseEvents,
            True,
        )
        self.control_tooltip.hide()

        self.back_button.clicked.connect(
            self.upcoming_requested.emit
        )
        self.back_button.hover_entered.connect(
            lambda: self._show_tooltip(
                self.back_button,
                "Back to upcoming",
            )
        )
        self.back_button.hover_left.connect(
            self._hide_tooltip
        )

        self.refresh_button.hover_entered.connect(
            lambda: self._show_tooltip(
                self.refresh_button,
                "Refresh now",
            )
        )
        self.refresh_button.hover_left.connect(
            self._hide_tooltip
        )

        self.lock_button.hover_entered.connect(
            self._show_lock_tooltip
        )
        self.lock_button.hover_left.connect(
            self._hide_tooltip
        )

        self.open_button.hover_entered.connect(
            lambda: self._show_tooltip(
                self.open_button,
                "Open Google Calendar",
            )
        )
        self.open_button.hover_left.connect(
            self._hide_tooltip
        )

        self.close_button.hover_entered.connect(
            lambda: self._show_tooltip(
                self.close_button,
                "Hide widget",
            )
        )
        self.close_button.hover_left.connect(
            self._hide_tooltip
        )

        # ============================================================
        # EVENT LIST
        # ============================================================

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(
            QScrollArea.NoFrame
        )
        self.scroll.setStyleSheet(
            SCROLL_AREA_STYLE
        )

        self.content = QWidget()
        self.content.setStyleSheet(
            TRANSPARENT_PANEL_STYLE
        )

        self.events_layout = QVBoxLayout(
            self.content
        )
        self.events_layout.setContentsMargins(
            0,
            0,
            5,
            0,
        )
        self.events_layout.setSpacing(6)

        self.scroll.setWidget(
            self.content
        )
        layout.addWidget(
            self.scroll
        )

        # ============================================================
        # SYNC STATUS
        # ============================================================

        self.sync_status = QLabel("")
        self.sync_status.setStyleSheet(
            """
            QLabel {
                color: #B8B8B8;
                background: transparent;
                border: none;

                font-family: "Segoe UI";
                font-size: 13px;
                font-weight: 500;

                padding: 4px 3px;
            }
            """
        )
        layout.addWidget(
            self.sync_status
        )


    def ensure_header_controls_visible(self) -> None:
        """Keep all permanent header controls visible after tray restore."""
        self.refresh_button.show()
        self.lock_button.show()
        self.open_button.show()
        self.close_button.show()
        self.close_button.raise_()

    def set_sync_status(
        self,
        text: str,
        warning: bool = False,
    ) -> None:
        color = (
            "#D6B36A"
            if warning
            else "#B8B8B8"
        )

        self.sync_status.setText(text)
        self.sync_status.setStyleSheet(
            f"""
            QLabel {{
                color: {color};
                background: transparent;
                border: none;

                font-family: "Segoe UI";
                font-size: 13px;
                font-weight: 500;

                padding: 4px 3px;
            }}
            """
        )

    def set_days_ahead(
        self,
        days: int,
    ) -> None:
        self.days_ahead = days
        self._render()

    def set_events(
        self,
        events: list[CalendarEvent],
    ) -> None:
        self._events = list(events)
        self._render()

    def show_date(
        self,
        selected_date: date,
    ) -> None:
        self._selected_date = selected_date
        self._render()

    def show_upcoming(self) -> None:
        self._selected_date = None
        self._render()

    # ================================================================
    # POSITION LOCK
    # ================================================================

    def _toggle_position_lock(self) -> None:
        self.position_locked = (
            not self.position_locked
        )

        self.lock_button.set_icon_name(
            "lock"
            if self.position_locked
            else "unlock"
        )
        # Blue unlocked icon communicates that reposition mode is active.
        self.lock_button.set_active(
            not self.position_locked
        )

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
            self.control_tooltip
            .sizeHint()
            .width()
        )
        tooltip_height = (
            self.control_tooltip
            .sizeHint()
            .height()
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

        x = max(0, x)

        if x + tooltip_width > self.width():
            x = (
                self.width()
                - tooltip_width
            )

        self.control_tooltip.resize(
            tooltip_width,
            tooltip_height,
        )
        self.control_tooltip.move(
            x,
            y,
        )
        self.control_tooltip.raise_()
        self.control_tooltip.show()

    def _hide_tooltip(self) -> None:
        self.control_tooltip.hide()

    # ================================================================
    # RENDERING
    # ================================================================

    def _render(self) -> None:
        self._clear_events()

        if self._selected_date is not None:
            self._render_selected_date()
        else:
            self._render_upcoming()

        self.scroll.verticalScrollBar().setValue(
            0
        )

    def _render_upcoming(self) -> None:
        self.back_button.hide()
        self.title.setText(
            self._title_text()
        )

        today = date.today()
        end_date = today + timedelta(
            days=self.days_ahead
        )

        upcoming = sorted(
            (
                event
                for event in self._events
                if (
                    today
                    <= event.event_date
                    < end_date
                )
            ),
            key=lambda event: event.sort_key(),
        )

        if not upcoming:
            self._show_empty(
                f"No events or tasks in the next "
                f"{self.days_ahead} days"
            )
            return

        self._add_event_cards(
            upcoming
        )

    def _render_selected_date(self) -> None:
        selected_date = self._selected_date

        if selected_date is None:
            return

        self.back_button.show()
        self.title.setText(
            selected_date
            .strftime("%a, %d %b")
            .upper()
        )

        day_items = sorted(
            (
                event
                for event in self._events
                if event.event_date
                == selected_date
            ),
            key=lambda event: event.sort_key(),
        )

        if not day_items:
            self._show_empty(
                "Nothing on this day"
            )
            return

        self._add_event_cards(
            day_items
        )

    def _add_event_cards(
        self,
        events: list[CalendarEvent],
    ) -> None:
        for event in events:
            self.events_layout.addWidget(
                EventCard(event)
            )

        self.events_layout.addStretch()

    def _show_empty(
        self,
        text: str,
    ) -> None:
        empty = QLabel(text)
        empty.setStyleSheet(
            EMPTY_STYLE
        )
        self.events_layout.addWidget(
            empty
        )
        self.events_layout.addStretch()

    def _clear_events(self) -> None:
        while self.events_layout.count():
            item = self.events_layout.takeAt(0)
            widget = item.widget()

            if widget:
                widget.deleteLater()

    def _title_text(self) -> str:
        return f"NEXT {self.days_ahead} DAYS"
