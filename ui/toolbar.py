from PyQt6.QtWidgets import QToolBar, QStyle, QLineEdit, QLabel, QWidget, QSizePolicy
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIntValidator
from core.state import DocumentState

class PDFToolBar(QToolBar):
    def __init__(self, state: DocumentState = None, parent=None):
        """
        Initialize the PDF Toolbar.
        """
        super().__init__("PDF Operations", parent)
        self.state = state
        self.setMovable(False)
        self.init_ui()
        self.connect_signals()
        
        # Initially disable document-specific controls until a document is loaded
        self.set_controls_enabled(False)
        
        if self.state:
            self.set_active_state(self.state)

    def init_ui(self) -> None:
        """
        Create and layout the toolbar widgets.
        """
        # 1. Open File Button (using system dialog icon)
        open_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_DialogOpenButton)
        self.open_action = QAction(open_icon, "Open PDF", self)
        self.open_action.setToolTip("Open a PDF file")
        self.addAction(self.open_action)

        # 1b. Document Outline Toggle
        self.outline_action = QAction("📖 Outline", self)
        self.outline_action.setCheckable(True)
        self.outline_action.setChecked(True)
        self.outline_action.setToolTip("Show/Hide Document Outline")
        self.addAction(self.outline_action)

        self.addSeparator()

        # 2. Navigation Group
        # Previous Page Button
        prev_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowLeft)
        self.prev_action = QAction(prev_icon, "Previous Page", self)
        self.prev_action.setToolTip("Previous Page")
        self.addAction(self.prev_action)

        # Page Input field
        self.page_input = QLineEdit()
        self.page_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_input.setToolTip("Current Page (Press Enter to Go)")
        # Limit to integers, range will be updated dynamically on doc load
        self.page_validator = QIntValidator(1, 9999, self)
        self.page_input.setValidator(self.page_validator)
        self.addWidget(self.page_input)

        # Total Pages Label
        self.page_label = QLabel("/ 0")
        self.addWidget(self.page_label)

        # Next Page Button
        next_icon = self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowRight)
        self.next_action = QAction(next_icon, "Next Page", self)
        self.next_action.setToolTip("Next Page")
        self.addAction(self.next_action)

        self.addSeparator()

        # 3. Zoom Group
        # Zoom Out Action (using Unicode character ➖)
        self.zoom_out_action = QAction("➖", self)
        self.zoom_out_action.setToolTip("Zoom Out")
        self.addAction(self.zoom_out_action)

        # Zoom Percentage Label
        self.zoom_label = QLabel("100%")
        self.zoom_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.zoom_label.setStyleSheet("padding: 0 4px; font-weight: bold;")
        self.addWidget(self.zoom_label)

        # Zoom In Action (using Unicode character ➕)
        self.zoom_in_action = QAction("➕", self)
        self.zoom_in_action.setToolTip("Zoom In")
        self.addAction(self.zoom_in_action)

        self.addSeparator()

        # 4. Fit Modes Group
        # Fit Width Action
        self.fit_width_action = QAction("↔️ Fit Width", self)
        self.fit_width_action.setToolTip("Fit page to window width")
        self.addAction(self.fit_width_action)

        # Fit Height Action
        self.fit_height_action = QAction("↕️ Fit Height", self)
        self.fit_height_action.setToolTip("Fit page to window height")
        self.addAction(self.fit_height_action)

        self.addSeparator()

        # 5. Text Extraction / AI Preparation Group
        self.extract_action = QAction("📝 Extract Text", self)
        self.extract_action.setToolTip("Extract all PDF text to a .txt file (AI-ready)")
        self.addAction(self.extract_action)

        # 5b. Notebook Toggle
        self.notebook_action = QAction("📓 Notebook", self)
        self.notebook_action.setCheckable(True)
        self.notebook_action.setChecked(True)
        self.notebook_action.setToolTip("Show/Hide Notebook & Notes")
        self.addAction(self.notebook_action)

        # 6. Spacer to push Theme Switcher to the far right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.addWidget(spacer)

        # 7. Toggle Theme Action (Initially displays moon for Dark Mode transition)
        self.theme_action = QAction("🌙 Theme", self)
        self.theme_action.setToolTip("Toggle Light/Dark Theme")
        self.addAction(self.theme_action)

    def connect_signals(self) -> None:
        """
        Connect actions/widgets and state signals.
        """
        # Connect UI actions to wrapper methods
        self.prev_action.triggered.connect(self.on_prev_page_clicked)
        self.next_action.triggered.connect(self.on_next_page_clicked)
        self.zoom_in_action.triggered.connect(self.on_zoom_in_clicked)
        self.zoom_out_action.triggered.connect(self.on_zoom_out_clicked)
        self.fit_width_action.triggered.connect(self.on_fit_width_clicked)
        self.fit_height_action.triggered.connect(self.on_fit_height_clicked)
        self.theme_action.triggered.connect(self.on_theme_clicked)

        # Connect QLineEdit return key
        self.page_input.returnPressed.connect(self.on_page_input_submitted)

    def set_active_state(self, state: DocumentState) -> None:
        """
        Switch the active document state managed by this toolbar.
        """
        # Disconnect old state signals if present
        if self.state:
            try:
                self.state.page_changed.disconnect(self.on_page_changed)
                self.state.zoom_changed.disconnect(self.on_zoom_changed)
                self.state.theme_changed.disconnect(self.on_theme_changed)
                self.state.document_loaded.disconnect(self.on_document_loaded)
                self.state.document_closed.disconnect(self.on_document_closed)
            except TypeError:
                pass
                
        self.state = state
        
        # Connect new state signals
        if self.state:
            self.state.page_changed.connect(self.on_page_changed)
            self.state.zoom_changed.connect(self.on_zoom_changed)
            self.state.theme_changed.connect(self.on_theme_changed)
            self.state.document_loaded.connect(self.on_document_loaded)
            self.state.document_closed.connect(self.on_document_closed)
            
            if self.state.is_loaded:
                self.on_document_loaded()
            else:
                self.on_document_closed()
        else:
            self.on_document_closed()

    def set_controls_enabled(self, enabled: bool) -> None:
        """
        Enable/disable page and zoom controls.
        """
        self.prev_action.setEnabled(enabled)
        self.next_action.setEnabled(enabled)
        self.page_input.setEnabled(enabled)
        self.zoom_out_action.setEnabled(enabled)
        self.zoom_in_action.setEnabled(enabled)
        self.fit_width_action.setEnabled(enabled)
        self.fit_height_action.setEnabled(enabled)
        self.extract_action.setEnabled(enabled)

    # Action Wrapper Slots
    def on_prev_page_clicked(self) -> None:
        if self.state:
            self.state.prev_page()

    def on_next_page_clicked(self) -> None:
        if self.state:
            self.state.next_page()

    def on_zoom_in_clicked(self) -> None:
        if self.state:
            self.state.zoom_in(0.1)

    def on_zoom_out_clicked(self) -> None:
        if self.state:
            self.state.zoom_out(0.1)

    def on_fit_width_clicked(self) -> None:
        if self.state:
            self.state.fit_mode = 'width'

    def on_fit_height_clicked(self) -> None:
        if self.state:
            self.state.fit_mode = 'height'

    def on_theme_clicked(self) -> None:
        if self.state:
            self.state.toggle_theme()

    # Slots responding to State changes
    def on_page_changed(self, page_index: int) -> None:
        if self.state:
            self.page_input.setText(str(page_index + 1))
            self.prev_action.setEnabled(page_index > 0)
            self.next_action.setEnabled(page_index < self.state.total_pages - 1)

    def on_zoom_changed(self, zoom_level: float) -> None:
        self.zoom_label.setText(f"{int(zoom_level * 100)}%")

    def on_theme_changed(self, theme: str) -> None:
        if theme == 'light':
            self.theme_action.setText("🌙 Theme")
            self.theme_action.setToolTip("Switch to Dark Theme")
        else:
            self.theme_action.setText("☀️ Theme")
            self.theme_action.setToolTip("Switch to Light Theme")

    def on_document_loaded(self) -> None:
        if self.state:
            self.set_controls_enabled(True)
            self.page_label.setText(f"/ {self.state.total_pages}")
            self.page_validator.setTop(self.state.total_pages)
            self.on_page_changed(self.state.current_page)
            self.on_zoom_changed(self.state.zoom_level)

    def on_document_closed(self) -> None:
        self.set_controls_enabled(False)
        self.page_input.clear()
        self.page_label.setText("/ 0")
        self.zoom_label.setText("100%")

    def on_page_input_submitted(self) -> None:
        """
        Jump to page entered in the LineEdit.
        """
        if self.state:
            text = self.page_input.text()
            if text:
                try:
                    page_num = int(text)
                    self.state.current_page = page_num - 1
                except ValueError:
                    self.on_page_changed(self.state.current_page)

