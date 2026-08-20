import sys
import ctypes

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication

from ui.calendar_widget import CalendarWidget


def create_app_icon() -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)

    painter.setBrush(QColor("#3B82F6"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(4, 4, 56, 56, 12, 12)

    painter.setBrush(QColor("#FFFFFF"))
    painter.drawRoundedRect(10, 10, 44, 12, 4, 4)

    painter.setPen(QColor("#FFFFFF"))
    painter.setFont(QFont("Segoe UI", 22, QFont.Bold))
    painter.drawText(
        pixmap.rect().adjusted(0, 12, 0, 0),
        Qt.AlignCenter,
        "20",
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

    widget = CalendarWidget()
    widget.setWindowIcon(icon)
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
