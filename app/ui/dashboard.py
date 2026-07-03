from PyQt6.QtWidgets import QMainWindow, QSplitter, QStatusBar, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from app.ui.chat_panel import ChatPanel
from app.ui.telemetry_panel import TelemetryPanel


class DashboardWindow(QMainWindow):
    # Main application window that splits the UI into chat and telemetry panels

    def __init__(self):
        super().__init__()
        self.setWindowTitle('🏎  F1 Race Engineer — AI Dashboard')
        self.setMinimumSize(1100, 700)
        self.resize(1400, 850)
        self._setup_ui()
        self._setup_statusbar()

    def _setup_ui(self):
        # Create horizontal splitter to partition left and right sections
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName('main_splitter')
        splitter.setHandleWidth(2)

        self.chat_panel = ChatPanel()
        self.telemetry_panel = TelemetryPanel()

        splitter.addWidget(self.chat_panel)
        splitter.addWidget(self.telemetry_panel)
        splitter.setSizes([480, 720])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        self.setCentralWidget(splitter)

    def _setup_statusbar(self):
        # Bottom status bar setup
        statusbar = QStatusBar()
        statusbar.setObjectName('main_statusbar')

        left = QLabel('🏎  F1 Race Engineer Dashboard')
        left.setFont(QFont('Segoe UI', 8))

        right = QLabel('PyQt6  •  Ollama / OpenAI  •  FastF1  •  Matplotlib')
        right.setFont(QFont('Segoe UI', 8))
        right.setObjectName('statusbar_right')

        statusbar.addWidget(left)
        statusbar.addPermanentWidget(right)
        self.setStatusBar(statusbar)
