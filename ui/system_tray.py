from __future__ import annotations

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


class SystemTray(QObject):
    show_requested = Signal()
    hide_requested = Signal()
    settings_requested = Signal()
    quit_requested = Signal()
    toggle_requested = Signal()

    def __init__(
        self,
        icon: QIcon,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)

        self.available = (
            QSystemTrayIcon.isSystemTrayAvailable()
        )

        self.tray = QSystemTrayIcon(
            icon,
            self,
        )
        self.tray.setToolTip(
            "Desktop Calendar"
        )

        self.menu = QMenu()

        self.show_action = QAction(
            "Show Calendar",
            self,
        )
        self.hide_action = QAction(
            "Hide Calendar",
            self,
        )
        self.settings_action = QAction(
            "Settings...",
            self,
        )
        self.quit_action = QAction(
            "Quit",
            self,
        )

        self.show_action.triggered.connect(
            self.show_requested.emit
        )
        self.hide_action.triggered.connect(
            self.hide_requested.emit
        )
        self.settings_action.triggered.connect(
            self.settings_requested.emit
        )
        self.quit_action.triggered.connect(
            self.quit_requested.emit
        )

        self.menu.addAction(
            self.show_action
        )
        self.menu.addAction(
            self.hide_action
        )
        self.menu.addSeparator()
        self.menu.addAction(
            self.settings_action
        )
        self.menu.addSeparator()
        self.menu.addAction(
            self.quit_action
        )

        self.tray.setContextMenu(
            self.menu
        )

        self.tray.activated.connect(
            self._handle_activation
        )

    def show(self) -> None:
        if self.available:
            self.tray.show()

    def set_widget_visible(
        self,
        visible: bool,
    ) -> None:
        self.show_action.setEnabled(
            not visible
        )
        self.hide_action.setEnabled(
            visible
        )

    def _handle_activation(
        self,
        reason: QSystemTrayIcon.ActivationReason,
    ) -> None:
        if reason in (
            QSystemTrayIcon.Trigger,
            QSystemTrayIcon.DoubleClick,
        ):
            self.toggle_requested.emit()
