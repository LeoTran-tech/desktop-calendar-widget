from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QTimer
from PySide6.QtGui import QGuiApplication, QScreen
from PySide6.QtWidgets import QApplication, QWidget

from utils.app_settings import AppSettings


class WindowPositionManager(QObject):
    """Persists window geometry and keeps the widget on an active monitor."""

    EDGE_MARGIN = 20
    SAVE_DELAY_MS = 250

    def __init__(
        self,
        window: QWidget,
        settings: AppSettings,
    ) -> None:
        super().__init__(window)

        self.window = window
        self.settings = settings
        self._restoring = False

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self.save_now)

        self.window.installEventFilter(self)

        app = QGuiApplication.instance()

        if app is not None:
            app.screenRemoved.connect(
                self._screen_configuration_changed
            )
            app.screenAdded.connect(
                self._screen_configuration_changed
            )

    def restore(self) -> None:
        self._restoring = True

        geometry = self.settings.get_window_geometry()

        if geometry:
            self.window.restoreGeometry(geometry)
        else:
            self.move_to_default_screen()

        self._restoring = False

        QTimer.singleShot(
            0,
            self.ensure_visible,
        )

    def move_to_default_screen(self) -> None:
        screen = self._preferred_screen()

        if screen is None:
            return

        area = screen.availableGeometry()

        self.window.move(
            area.right()
            - self.window.width()
            - self.EDGE_MARGIN
            + 1,
            area.top() + self.EDGE_MARGIN,
        )

        self.schedule_save()

    def ensure_visible(self) -> None:
        screens = QApplication.screens()

        if not screens:
            return

        frame = self.window.frameGeometry()

        best_screen = None
        best_area = 0

        for screen in screens:
            visible = frame.intersected(
                screen.availableGeometry()
            )
            area = max(0, visible.width()) * max(
                0,
                visible.height(),
            )

            if area > best_area:
                best_area = area
                best_screen = screen

        if best_screen is None or best_area == 0:
            # The saved monitor may have been unplugged. Move the widget
            # to an active monitor instead of leaving it off-screen.
            self.move_to_default_screen()
            return

        # Clamp the restored position into the active monitor's usable
        # area. This also handles resolution or taskbar-layout changes.
        area = best_screen.availableGeometry()

        x = min(
            max(frame.x(), area.left()),
            max(area.left(), area.right() - self.window.width() + 1),
        )
        y = min(
            max(frame.y(), area.top()),
            max(area.top(), area.bottom() - self.window.height() + 1),
        )

        if x != frame.x() or y != frame.y():
            self._restoring = True
            self.window.move(x, y)
            self._restoring = False

        self.schedule_save()

    def save_now(self) -> None:
        if self._restoring:
            return

        self.settings.set_window_geometry(
            self.window.saveGeometry()
        )

        screen = self.window.screen()

        if screen is not None:
            self.settings.set_screen_name(
                screen.name()
            )

        self.settings.sync()

    def schedule_save(self) -> None:
        if self._restoring:
            return

        self._save_timer.start(
            self.SAVE_DELAY_MS
        )

    def eventFilter(self, obj, event):
        if (
            obj is self.window
            and event.type()
            in (QEvent.Move, QEvent.Resize)
        ):
            self.schedule_save()

        return super().eventFilter(obj, event)

    def _preferred_screen(self) -> QScreen | None:
        saved_name = self.settings.get_screen_name()

        for screen in QApplication.screens():
            if screen.name() == saved_name:
                return screen

        return QApplication.primaryScreen()

    def _screen_configuration_changed(
        self,
        _screen: QScreen,
    ) -> None:
        QTimer.singleShot(
            0,
            self.ensure_visible,
        )
