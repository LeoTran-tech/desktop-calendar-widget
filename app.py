import ctypes
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QDialog

from ui.calendar_widget import CalendarWidget
from ui.dialogs.first_run_setup_dialog import FirstRunSetupDialog
from ui.system_tray import SystemTray
from utils.app_settings import AppSettings
from utils.windows_startup import enable_auto_start


def create_app_icon() -> QIcon:
    """Create a simple calendar icon that stays readable in the system tray."""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    # Blue app tile.
    painter.setBrush(QColor("#3B82F6"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(
        4,
        4,
        56,
        56,
        12,
        12,
    )

    # White calendar body.
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(
        13,
        15,
        38,
        36,
        6,
        6,
    )

    # Blue header strip cut into the white calendar body.
    painter.setBrush(QColor("#3B82F6"))
    painter.drawRoundedRect(
        13,
        15,
        38,
        11,
        6,
        6,
    )
    painter.drawRect(
        13,
        21,
        38,
        5,
    )

    # Calendar binding rings.
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(
        20,
        9,
        5,
        12,
        2,
        2,
    )
    painter.drawRoundedRect(
        39,
        9,
        5,
        12,
        2,
        2,
    )

    # Small blue date blocks. No fixed day number, so the icon stays generic.
    painter.setBrush(QColor("#3B82F6"))
    for x in (20, 31, 42):
        for y in (31, 41):
            painter.drawRoundedRect(
                x,
                y,
                6,
                6,
                2,
                2,
            )

    painter.end()

    return QIcon(pixmap)


def main() -> None:
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "LeoTran.DesktopCalendarWidget.2.0"
        )
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    icon = create_app_icon()
    app.setWindowIcon(icon)

    settings = AppSettings()

    # First install: complete Google OAuth + browser sign-in before the
    # CalendarWidget is created. This prevents the scraper from launching
    # headlessly before the user has signed in.
    if not settings.is_setup_complete():
        setup_dialog = FirstRunSetupDialog()

        if setup_dialog.exec() != QDialog.Accepted:
            return

    # Only register Windows auto-start after first-time setup succeeds.
    enable_auto_start()

    widget = CalendarWidget()
    widget.setWindowIcon(icon)

    tray = SystemTray(
        icon,
        app,
    )

    if tray.available:
        app.setQuitOnLastWindowClosed(False)

        tray.show_requested.connect(
            widget.show_from_tray
        )
        tray.hide_requested.connect(
            widget.hide
        )
        tray.toggle_requested.connect(
            widget.toggle_visibility
        )
        tray.settings_requested.connect(
            widget.open_settings
        )
        tray.quit_requested.connect(
            app.quit
        )
        widget.visibility_changed.connect(
            tray.set_widget_visible
        )

        tray.show()
    else:
        app.setQuitOnLastWindowClosed(True)

    app.aboutToQuit.connect(
        widget.position_manager.save_now
    )

    widget.show()
    tray.set_widget_visible(True)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
