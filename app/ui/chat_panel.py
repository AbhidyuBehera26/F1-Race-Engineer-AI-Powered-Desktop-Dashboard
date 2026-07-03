import re
import html as html_module

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

# Background LLM thread import
from app.backend.engineer import LLMWorkerThread


def _md_to_html(text: str) -> str:
    # Basic helper to convert markdown syntax to HTML tags for QLabel text
    text = html_module.escape(text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*(.*?)\*',     r'<i>\1</i>', text)
    text = re.sub(
        r'`([^`]+)`',
        r'<code style="background:#1a1a1a;padding:1px 4px;border-radius:3px;">\1</code>',
        text
    )
    text = text.replace('\n', '<br>')
    text = re.sub(r'<br>- ', '<br>• ', text)
    return text


class MessageBubble(QFrame):
    # Chat message bubble. User messages align right (red), assistant aligns left (dark).

    def __init__(self, text: str, role: str, parent=None):
        super().__init__(parent)
        self.setObjectName(f'bubble_{role}')

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 4, 0, 4)

        bubble = QFrame()
        bubble.setObjectName(f'inner_bubble_{role}')
        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(12, 10, 12, 10)
        inner.setSpacing(4)

        if role in ('user', 'assistant'):
            role_label = QLabel('YOU' if role == 'user' else '🏎  RACE ENGINEER')
            role_label.setObjectName(f'role_label_{role}')
            role_label.setFont(QFont('Segoe UI', 8, QFont.Weight.Bold))
            inner.addWidget(role_label)

        msg = QLabel(_md_to_html(text))
        msg.setObjectName(f'msg_label_{role}')
        msg.setWordWrap(True)
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setFont(QFont('Segoe UI', 10))
        msg.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        inner.addWidget(msg)

        if role == 'user':
            bubble.setMaximumWidth(480)
            outer.addStretch()
            outer.addWidget(bubble)
        elif role == 'assistant':
            bubble.setMaximumWidth(520)
            outer.addWidget(bubble)
            outer.addStretch()
        else:
            bubble.setMaximumWidth(600)
            outer.addStretch()
            outer.addWidget(bubble)
            outer.addStretch()


class LoadingBubble(QFrame):
    # Thinking... animation shown while LLM is generating a response

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName('bubble_loading')
        self._dots = 0

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)

        bubble = QFrame()
        bubble.setObjectName('inner_bubble_loading')
        bubble.setMaximumWidth(200)
        inner = QVBoxLayout(bubble)
        inner.setContentsMargins(12, 10, 12, 10)

        self._label = QLabel('🏎  Thinking.')
        self._label.setObjectName('loading_label')
        self._label.setFont(QFont('Segoe UI', 10))
        inner.addWidget(self._label)

        layout.addWidget(bubble)
        layout.addStretch()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.start(400)

    def _animate(self):
        self._dots = (self._dots + 1) % 4
        self._label.setText('🏎  Thinking' + '.' * self._dots)

    def set_status(self, text: str):
        self._label.setText(f'⚙ {text}')

    def stop(self):
        self._timer.stop()


class ChatPanel(QWidget):
    # Left hand panel representing the AI assistant conversation view

    def __init__(self, parent=None):
        super().__init__(parent)
        self._history        = []
        self._is_processing  = False
        self._loading_bubble = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Chat Panel Header
        header = QFrame()
        header.setObjectName('panel_header')
        header.setFixedHeight(68)
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 10, 20, 8)
        header_layout.setSpacing(3)

        title = QLabel('🏎  CHIEF RACE ENGINEER')
        title.setFont(QFont('Segoe UI', 11, QFont.Weight.Bold))
        title.setObjectName('panel_title')

        self.backend_label = QLabel('● Detecting AI backend...')
        self.backend_label.setObjectName('backend_label')
        self.backend_label.setFont(QFont('Segoe UI', 8))

        header_layout.addWidget(title)
        header_layout.addWidget(self.backend_label)

        # Quick suggest buttons
        suggestions_frame = QFrame()
        suggestions_frame.setObjectName('suggestions_frame')
        suggestions_layout = QHBoxLayout(suggestions_frame)
        suggestions_layout.setContentsMargins(12, 6, 12, 6)
        suggestions_layout.setSpacing(8)

        for text in ["Tyres for Spa today?", "Analyse the brake zones", "Best aero for Monza?"]:
            btn = QPushButton(text)
            btn.setObjectName('suggestion_btn')
            btn.setFont(QFont('Segoe UI', 8))
            btn.clicked.connect(lambda checked, t=text: self._send(t))
            suggestions_layout.addWidget(btn)

        # Scroll area for bubbles
        self.scroll_area = QScrollArea()
        self.scroll_area.setObjectName('chat_scroll')
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.chat_container = QWidget()
        self.chat_container.setObjectName('chat_container')
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(16, 16, 16, 16)
        self.chat_layout.setSpacing(4)
        self.chat_layout.addStretch()

        self.scroll_area.setWidget(self.chat_container)

        self._add_bubble(
            "Ready for debrief. Ask about tyre strategy, car setup, or telemetry analysis.\n"
            "I have live weather for 10 circuits and the full F1 engineering reference.",
            role='assistant'
        )

        # Input box and send button
        input_frame = QFrame()
        input_frame.setObjectName('input_frame')
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 12, 16, 14)
        input_layout.setSpacing(10)

        self.input_field = QLineEdit()
        self.input_field.setObjectName('input_field')
        self.input_field.setPlaceholderText('Ask your race engineer...')
        self.input_field.setFont(QFont('Segoe UI', 10))
        self.input_field.setFixedHeight(40)
        self.input_field.returnPressed.connect(self._on_send_clicked)

        self.send_btn = QPushButton('▶')
        self.send_btn.setObjectName('send_btn')
        self.send_btn.setFixedSize(40, 40)
        self.send_btn.setFont(QFont('Segoe UI', 12))
        self.send_btn.clicked.connect(self._on_send_clicked)

        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)

        layout.addWidget(header)
        layout.addWidget(suggestions_frame)
        layout.addWidget(self.scroll_area, stretch=1)
        layout.addWidget(input_frame)

    def _add_bubble(self, text: str, role: str) -> MessageBubble:
        bubble = MessageBubble(text, role)
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)
        return bubble

    def _add_loading(self) -> LoadingBubble:
        bubble = LoadingBubble()
        self.chat_layout.insertWidget(self.chat_layout.count() - 1, bubble)
        QTimer.singleShot(50, self._scroll_to_bottom)
        return bubble

    def _remove_loading(self):
        if self._loading_bubble:
            self._loading_bubble.stop()
            self._loading_bubble.setParent(None)
            self._loading_bubble.deleteLater()
            self._loading_bubble = None

    def _scroll_to_bottom(self):
        sb = self.scroll_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _on_send_clicked(self):
        text = self.input_field.text().strip()
        if text:
            self._send(text)

    def _send(self, message: str):
        # Disable inputs and send request to backend thread
        if self._is_processing:
            return

        self._is_processing = True
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)

        # Show user message and thinking indicator
        self._add_bubble(message, role='user')
        self._loading_bubble = self._add_loading()

        # Start background worker thread
        self.worker_thread = LLMWorkerThread(message, self._history.copy())
        
        # Connect thread signals
        self.worker_thread.finished.connect(self._on_response)
        self.worker_thread.status_updated.connect(self._on_status)
        self.worker_thread.error_occurred.connect(self._on_error)
        
        self.worker_thread.start()

    def _on_status(self, message: str):
        if self._loading_bubble:
            self._loading_bubble.set_status(message)

    def _on_response(self, response: str, backend: str):
        self._remove_loading()
        self._add_bubble(response, role='assistant')
        self._history.append({"role": "assistant", "content": response})

        self.backend_label.setText(f'● {backend}')
        self.backend_label.setStyleSheet('color: #00e676;')

        self._is_processing = False
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()

    def _on_error(self, error: str):
        self._remove_loading()
        self._add_bubble(f'⚠ Error: {error}', role='status')
        self.backend_label.setText('● Disconnected')
        self.backend_label.setStyleSheet('color: #e10600;')

        self._is_processing = False
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
