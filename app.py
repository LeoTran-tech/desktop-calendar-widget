import sys
from PySide6.QtWidgets import QApplication
from ui.calendar_widget import CalendarWidget

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    widget = CalendarWidget()
    widget.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
