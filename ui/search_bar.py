from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QStyle
from PyQt6.QtCore import pyqtSignal, Qt

class PDFSearchBar(QWidget):
    # Signals to communicate search requests to MainWindow
    search_requested = pyqtSignal(str, bool)  # (search_term, search_forward)
    search_cleared = pyqtSignal()
    close_requested = pyqtSignal()

    def __init__(self, parent=None):
        """
        Initialize the PDF Search Bar.
        """
        super().__init__(parent)
        self.init_ui()
        self.connect_signals()

    def init_ui(self) -> None:
        """
        Setup the layout and components of the search bar.
        """
        layout = QHBoxLayout()
        layout.setContentsMargins(15, 4, 15, 4)
        layout.setSpacing(8)
        self.setLayout(layout)

        # 1. Search Icon / Label
        self.search_label = QLabel("🔍 Find:")
        layout.addWidget(self.search_label)

        # 2. Input Field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter word or phrase...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setMaximumWidth(350)
        layout.addWidget(self.search_input)

        # 3. Status Label (matches indicator)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #777777; font-weight: bold; padding: 0 5px;")
        layout.addWidget(self.status_label)

        # 4. Find Previous Button
        self.btn_prev = QPushButton("🔼 Prev")
        self.btn_prev.setToolTip("Find Previous (Shift+Enter)")
        layout.addWidget(self.btn_prev)

        # 5. Find Next Button
        self.btn_next = QPushButton("🔽 Next")
        self.btn_next.setToolTip("Find Next (Enter)")
        layout.addWidget(self.btn_next)

        # 6. Close Button
        self.btn_close = QPushButton("✖")
        self.btn_close.setToolTip("Close Search Bar (Esc)")
        self.btn_close.setFlat(True)
        self.btn_close.setMaximumWidth(30)
        layout.addWidget(self.btn_close)

        # Apply specific styling for search bar to fit both Light and Dark themes
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            QPushButton {
                border: 1px solid transparent;
                border-radius: 4px;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background-color: rgba(128, 128, 128, 0.2);
            }
        """)

    def connect_signals(self) -> None:
        """
        Connect signals and slots.
        """
        # When pressing enter in the text box, trigger a next search
        self.search_input.returnPressed.connect(lambda: self.on_search_action(True))
        
        # Connect buttons
        self.btn_next.clicked.connect(lambda: self.on_search_action(True))
        self.btn_prev.clicked.connect(lambda: self.on_search_action(False))
        self.btn_close.clicked.connect(self.close_requested.emit)
        
        # When text is changed, if it becomes empty, clear highlights
        self.search_input.textChanged.connect(self.on_text_changed)

    def on_search_action(self, forward: bool) -> None:
        """
        Triggered when search is executed.
        """
        text = self.search_input.text()
        if text:
            self.search_requested.emit(text, forward)

    def on_text_changed(self, text: str) -> None:
        """
        Triggered when search query changes.
        """
        if not text:
            self.status_label.clear()
            self.search_cleared.emit()

    def set_result_status(self, current: int, total: int) -> None:
        """
        Update the match count label.
        """
        if total > 0:
            self.status_label.setText(f"{current} of {total} matches")
            self.status_label.setStyleSheet("color: #0071e3; font-weight: bold;")
        else:
            if self.search_input.text():
                self.status_label.setText("No matches")
                self.status_label.setStyleSheet("color: #ff3333; font-weight: bold;")
            else:
                self.status_label.clear()

    def focus_input(self) -> None:
        """
        Helper to focus the search bar input and select all text.
        """
        self.search_input.setFocus()
        self.search_input.selectAll()
