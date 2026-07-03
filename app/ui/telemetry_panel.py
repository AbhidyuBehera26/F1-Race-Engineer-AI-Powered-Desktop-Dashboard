from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont

# Load the background telemetry worker thread and output graph path
from app.backend.telemetry import TelemetryThread, GRAPH_PATH


class TelemetryPanel(QWidget):
    # Right-hand panel for showing Matplotlib graph using QPixmap

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_existing_graph()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Panel Header
        header = QFrame()
        header.setObjectName('panel_header')
        header.setFixedHeight(56)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 16, 0)

        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        title = QLabel('📊  LIVE TELEMETRY')
        title.setFont(QFont('Segoe UI', 11, QFont.Weight.Bold))
        title.setObjectName('panel_title')

        subtitle = QLabel('Spa-Francorchamps 2024 — Fastest Race Lap')
        subtitle.setObjectName('panel_subtitle')
        subtitle.setFont(QFont('Segoe UI', 9))

        title_col.addWidget(title)
        title_col.addWidget(subtitle)

        self.refresh_btn = QPushButton('🔄  Refresh')
        self.refresh_btn.setObjectName('refresh_btn')
        self.refresh_btn.setFixedSize(110, 34)
        self.refresh_btn.clicked.connect(self.refresh_telemetry)

        header_layout.addLayout(title_col)
        header_layout.addStretch()
        header_layout.addWidget(self.refresh_btn)

        # Telemetry Graph display
        graph_container = QFrame()
        graph_container.setObjectName('graph_container')
        graph_layout = QVBoxLayout(graph_container)
        graph_layout.setContentsMargins(16, 16, 16, 16)

        self.graph_label = QLabel('Loading telemetry data...')
        self.graph_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.graph_label.setObjectName('graph_label')
        self.graph_label.setMinimumHeight(300)
        graph_layout.addWidget(self.graph_label)

        # Status Bar
        status_bar = QFrame()
        status_bar.setObjectName('status_bar')
        status_bar.setFixedHeight(36)
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(20, 0, 20, 0)

        self.status_label = QLabel('Ready')
        self.status_label.setObjectName('status_label')
        self.status_label.setFont(QFont('Segoe UI', 9))
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        layout.addWidget(header)
        layout.addWidget(graph_container, stretch=1)
        layout.addWidget(status_bar)

    def _load_existing_graph(self):
        # Load existing graph file on startup if it exists
        paths_to_check = [GRAPH_PATH, Path(__file__).parent.parent.parent / 'telemetry_graph.png']
        for path in paths_to_check:
            if path.exists():
                self._display_graph(str(path))
                self.status_label.setText(f'✓  Loaded: {path.name}')
                return
        self.status_label.setText('No graph found — click Refresh to generate one')

    def refresh_telemetry(self):
        # Request new graph calculation in the background QThread
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText('⏳ Loading...')
        self.status_label.setText('Fetching FastF1 data...')

        self.telemetry_thread = TelemetryThread()
        
        # Connect thread callback events
        self.telemetry_thread.finished.connect(self._on_graph_ready)
        self.telemetry_thread.error_occurred.connect(self._on_error)
        self.telemetry_thread.status_updated.connect(self.status_label.setText)
        
        self.telemetry_thread.start()

    def _display_graph(self, path: str):
        # Load the graph image file and scale it to fit the panel
        pixmap = QPixmap(path)
        if pixmap.isNull():
            self.graph_label.setText(f'Could not load: {path}')
            return

        size = self.graph_label.size()
        if size.width() > 0 and size.height() > 0:
            pixmap = pixmap.scaled(
                size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        self.graph_label.setPixmap(pixmap)

    def _on_graph_ready(self, path: str):
        self._display_graph(path)
        self.status_label.setText(f'✓  Updated at {datetime.now().strftime("%H:%M:%S")}')
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText('🔄  Refresh')

    def _on_error(self, error: str):
        self.status_label.setText(f'⚠  {error}')
        self.graph_label.setText(f'Error:\n{error}')
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText('🔄  Retry')

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.graph_label.pixmap() and not self.graph_label.pixmap().isNull():
            if GRAPH_PATH.exists():
                self._display_graph(str(GRAPH_PATH))
