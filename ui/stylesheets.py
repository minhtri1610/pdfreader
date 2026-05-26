# High-quality QSS stylesheets for Light and Dark modes.
# Comments are in English.

LIGHT_STYLE = """
QMainWindow {
    background-color: #f5f5f7;
}

QToolBar {
    background-color: #ffffff;
    border-bottom: 1px solid #e5e5ea;
    spacing: 8px;
    padding: 6px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 10px;
    color: #1d1d1f;
    font-size: 13px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #f5f5f7;
    border-color: #d2d2d7;
}

QToolButton:pressed {
    background-color: #e8e8ed;
}

QLineEdit {
    background-color: #ffffff;
    border: 1px solid #d2d2d7;
    border-radius: 4px;
    padding: 3px 6px;
    color: #1d1d1f;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #0071e3;
}

QLabel {
    color: #1d1d1f;
    font-size: 13px;
}

QScrollArea {
    border: none;
    background-color: #f0f0f2;
}

/* QDockWidget (Sidebar) Styling */
QDockWidget {
    border: 1px solid #e5e5ea;
    color: #1d1d1f;
    font-weight: bold;
}

QDockWidget::title {
    background-color: #ffffff;
    padding-left: 10px;
    padding-top: 6px;
    padding-bottom: 6px;
    border-bottom: 1px solid #e5e5ea;
}

QTreeWidget {
    background-color: #ffffff;
    color: #1d1d1f;
    border: none;
}

QTreeWidget::item {
    padding: 6px;
    border-radius: 4px;
}

QTreeWidget::item:hover {
    background-color: #f5f5f7;
}

QTreeWidget::item:selected {
    background-color: #e8f2ff;
    color: #0071e3;
}

/* QListWidget (Notebook Sidebar) Styling */
QListWidget {
    background-color: #ffffff;
    color: #1d1d1f;
    border: none;
}

QListWidget::item {
    border-bottom: 1px solid #e5e5ea;
    padding: 2px;
}

QListWidget::item:hover {
    background-color: #f5f5f7;
}

QListWidget::item:selected {
    background-color: #e8f2ff;
}

/* Search Bar Area */
#SearchBarContainer {
    background-color: #ffffff;
    border-bottom: 1px solid #e5e5ea;
}

#SearchBarContainer QPushButton {
    background-color: #f5f5f7;
    border: 1px solid #d2d2d7;
    border-radius: 4px;
    color: #1d1d1f;
    font-size: 12px;
}

#SearchBarContainer QPushButton:hover {
    background-color: #e8e8ed;
    border-color: #8e8e93;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #f5f5f7;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #c1c1c1;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #a8a8a8;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #f5f5f7;
    height: 10px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #c1c1c1;
    border-radius: 5px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #a8a8a8;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
    width: 0px;
}
"""

DARK_STYLE = """
QMainWindow {
    background-color: #1e1e1e;
}

QToolBar {
    background-color: #2d2d2d;
    border-bottom: 1px solid #3d3d3d;
    spacing: 8px;
    padding: 6px;
}

QToolButton {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 10px;
    color: #e0e0e0;
    font-size: 13px;
    font-weight: 500;
}

QToolButton:hover {
    background-color: #3d3d3d;
    border-color: #555555;
}

QToolButton:pressed {
    background-color: #4a4a4a;
}

QLineEdit {
    background-color: #1e1e1e;
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 3px 6px;
    color: #e0e0e0;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #0a84ff;
}

QLabel {
    color: #e0e0e0;
    font-size: 13px;
}

QScrollArea {
    border: none;
    background-color: #121212;
}

/* QDockWidget (Sidebar) Styling */
QDockWidget {
    border: 1px solid #3d3d3d;
    color: #e0e0e0;
    font-weight: bold;
}

QDockWidget::title {
    background-color: #2d2d2d;
    padding-left: 10px;
    padding-top: 6px;
    padding-bottom: 6px;
    border-bottom: 1px solid #3d3d3d;
}

QTreeWidget {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: none;
}

QTreeWidget::item {
    padding: 6px;
    border-radius: 4px;
}

QTreeWidget::item:hover {
    background-color: #3d3d3d;
}

QTreeWidget::item:selected {
    background-color: #1a4572;
    color: #ffffff;
}

/* QListWidget (Notebook Sidebar) Styling */
QListWidget {
    background-color: #2d2d2d;
    color: #e0e0e0;
    border: none;
}

QListWidget::item {
    border-bottom: 1px solid #3d3d3d;
    padding: 2px;
}

QListWidget::item:hover {
    background-color: #3d3d3d;
}

QListWidget::item:selected {
    background-color: #1a4572;
}

/* Search Bar Area */
#SearchBarContainer {
    background-color: #2d2d2d;
    border-bottom: 1px solid #3d3d3d;
}

#SearchBarContainer QPushButton {
    background-color: #1e1e1e;
    border: 1px solid #555555;
    border-radius: 4px;
    color: #e0e0e0;
    font-size: 12px;
}

#SearchBarContainer QPushButton:hover {
    background-color: #3d3d3d;
    border-color: #888888;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #2d2d2d;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #555555;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #686868;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
    height: 0px;
}

QScrollBar:horizontal {
    border: none;
    background: #2d2d2d;
    height: 10px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #555555;
    border-radius: 5px;
    min-width: 20px;
}

QScrollBar::handle:horizontal:hover {
    background: #686868;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    border: none;
    background: none;
    width: 0px;
}
"""
