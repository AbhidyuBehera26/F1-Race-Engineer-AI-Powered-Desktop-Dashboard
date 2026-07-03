# Main entry point for the F1 Race Engineer desktop app.
# Starts PyQt, loads custom styling, and shows the dashboard window.

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from app.ui.dashboard import DashboardWindow

# Custom stylesheet to style the PyQt widgets with an F1 dark mode theme
STYLESHEET = """
/* Main window styling */
QMainWindow, QWidget {
    background-color: #0f0f0f;
    color: #e8e8e8;
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 13px;
}

/* Splitter handle */
QSplitter::handle            { background-color: #2a2a2a; }
QSplitter::handle:hover      { background-color: #e10600; }

/* Panel headers */
#panel_header                { background-color: #141414; border-bottom: 1px solid #2a2a2a; }
#panel_title                 { color: #ffffff; font-weight: bold; }
#panel_subtitle              { color: #888888; }

/* Quick suggestions */
#suggestions_frame           { background-color: #0f0f0f; border-bottom: 1px solid #1e1e1e; }
#suggestion_btn              { background-color: #1e1e1e; color: #aaaaaa; border: 1px solid #2e2e2e; border-radius: 12px; padding: 4px 12px; font-size: 11px; }
#suggestion_btn:hover        { background-color: #2a2a2a; color: #ffffff; border-color: #e10600; }

/* Scrollbars and chat area */
#chat_scroll                 { background-color: #0a0a0a; border: none; }
#chat_container              { background-color: #0a0a0a; }
QScrollBar:vertical          { background-color: #111111; width: 6px; margin: 0; }
QScrollBar::handle:vertical  { background-color: #333333; border-radius: 3px; min-height: 20px; }
QScrollBar::handle:vertical:hover { background-color: #e10600; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }

/* User chat bubble */
#inner_bubble_user           { background-color: #c00400; border-radius: 12px 12px 3px 12px; }
#role_label_user             { color: #ffaaaa; font-size: 9px; font-weight: bold; }
#msg_label_user              { color: #ffffff; }

/* AI chat bubble */
#inner_bubble_assistant      { background-color: #1a1a1a; border-left: 3px solid #e10600; border-radius: 3px 12px 12px 12px; }
#role_label_assistant        { color: #e10600; font-size: 9px; font-weight: bold; }
#msg_label_assistant         { color: #e8e8e8; }

/* System updates bubble */
#inner_bubble_status         { background-color: #141414; border: 1px solid #2a2a2a; border-radius: 8px; }
#msg_label_status            { color: #888888; font-size: 11px; }

/* Loading bubble */
#inner_bubble_loading        { background-color: #1a1a1a; border-left: 3px solid #444444; border-radius: 3px 12px 12px 12px; }
#loading_label               { color: #888888; }

/* Text input area */
#input_frame                 { background-color: #141414; border-top: 1px solid #2a2a2a; }
#input_field                 { background-color: #1e1e1e; color: #ffffff; border: 1px solid #333333; border-radius: 20px; padding: 8px 16px; font-size: 13px; }
#input_field:focus           { border-color: #e10600; background-color: #222222; }
#send_btn                    { background-color: #e10600; color: white; border: none; border-radius: 20px; font-size: 14px; font-weight: bold; }
#send_btn:hover              { background-color: #ff1a14; }
#send_btn:pressed            { background-color: #a00400; }
#send_btn:disabled           { background-color: #3a3a3a; color: #666666; }

#backend_label               { color: #00e676; font-size: 9px; }

/* Telemetry graph placeholder */
#graph_container             { background-color: #0a0a0a; }
#graph_label                 { color: #666666; }

/* Refresh button */
#refresh_btn                 { background-color: #1e1e1e; color: #e8e8e8; border: 1px solid #333333; border-radius: 6px; font-size: 12px; font-weight: bold; }
#refresh_btn:hover           { background-color: #e10600; border-color: #e10600; color: white; }
#refresh_btn:disabled        { color: #555555; border-color: #222222; }

/* Bottom status bar */
#status_bar                  { background-color: #141414; border-top: 1px solid #2a2a2a; }
#status_label                { color: #666666; }
QStatusBar                   { background-color: #141414; color: #555555; border-top: 1px solid #1e1e1e; }
#statusbar_right             { color: #333333; }
#main_splitter               { background-color: #0f0f0f; }
"""


def main():
    # Enable high-DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Initialize the PyQt app
    app = QApplication(sys.argv)
    app.setApplicationName('F1 Race Engineer')
    app.setApplicationVersion('2.0')
    
    # Apply stylesheet
    app.setStyleSheet(STYLESHEET)

    # Show dashboard
    window = DashboardWindow()
    window.show()
    
    # Start the Qt execution loop
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
