import sys
from pathlib import Path
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from app.ui.dashboard import DashboardWindow


def main():
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName('F1 Race Engineer')
    app.setApplicationVersion('2.0')

    qss_path = Path(__file__).parent / 'ui' / 'styles.qss'
    if qss_path.exists():
        app.setStyleSheet(qss_path.read_text(encoding='utf-8'))

    window = DashboardWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
