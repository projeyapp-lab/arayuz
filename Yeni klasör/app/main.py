from pathlib import Path

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from presentation.windows.main_window import MainWindow


def main():
    app = QApplication([])
    app.setFont(QFont("Segoe UI", 10))

    qss_path = Path(__file__).resolve().parent.parent / "styles" / "app.qss"
    if qss_path.exists():
        with open(qss_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    win = MainWindow()
    win.show()
    app.exec()


if __name__ == "__main__":
    main()
