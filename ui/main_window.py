import os
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QWidget, QVBoxLayout, QMessageBox, QInputDialog, QTabWidget, QLabel, QApplication, QToolButton, QTabBar
from PyQt6.QtCore import Qt, QRectF, QEvent, QTimer
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence, QPainter, QColor, QIcon, QDragEnterEvent, QDragMoveEvent, QDropEvent
from core.state import DocumentState
from ui.toolbar import PDFToolBar
from ui.sidebar import PDFSidebar
from ui.search_bar import PDFSearchBar
from ui.notebook_sidebar import PDFNotebookSidebar
from ui.stylesheets import LIGHT_STYLE, DARK_STYLE
from ui.tab_widget import PDFTab

class MainWindow(QMainWindow):
    def __init__(self):
        """
        Initialize the Main Window.
        """
        super().__init__()
        # Global application state (principally manages theme and global settings)
        self.state = DocumentState()
        self.active_tab = None
        
        self.init_ui()
        self.connect_signals()
        self.setup_shortcuts()
        
        # Apply initial theme (Light Mode)
        self.apply_theme(self.state.theme)

    def init_ui(self) -> None:
        """
        Setup the UI components with explicit parenting to avoid C++ garbage collection.
        """
        self.setWindowTitle("Kailash PDF Reader")
        self.resize(1200, 800)

        # Set window icon using the generated logo
        if os.path.exists("K.png"):
            self.setWindowIcon(QIcon("K.png"))

        # 1. Custom PDF Toolbar
        self.toolbar = PDFToolBar(self.state, self)
        self.addToolBar(self.toolbar)

        # 2. Main Central Container (explicitly parented to self)
        self.central_container = QWidget(self)
        self.container_layout = QVBoxLayout(self.central_container)
        self.container_layout.setContentsMargins(0, 0, 0, 0)
        self.container_layout.setSpacing(0)

        # Create Search Bar inside a styled container (explicitly parented to central_container)
        self.search_container = QWidget(self.central_container)
        self.search_container.setObjectName("SearchBarContainer")
        self.search_layout = QVBoxLayout(self.search_container)
        self.search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_bar = PDFSearchBar(self.search_container)
        self.search_layout.addWidget(self.search_bar)
        self.search_container.setVisible(False)
        self.container_layout.addWidget(self.search_container)

        # Create QTabWidget as central display area (explicitly parented to central_container)
        self.tab_widget = QTabWidget(self.central_container)
        self.tab_widget.setTabsClosable(False)
        self.container_layout.addWidget(self.tab_widget)

        # Welcome placeholder screen (explicitly parented to central_container)
        self.welcome_widget = QWidget(self.central_container)
        self.welcome_layout = QVBoxLayout(self.welcome_widget)
        self.welcome_label = QLabel(self.welcome_widget)
        self.welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.welcome_layout.addWidget(self.welcome_label)
        self.container_layout.addWidget(self.welcome_widget)

        # 3. Create PDF Sidebar - Document Outline (Left Dock Widget)
        # It is initialized with default settings and will switch dynamic state on tab changes
        self.sidebar = PDFSidebar(self.state, None, self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        # 4. Create PDF Notebook Sidebar - Highlights & Notes (Right Dock Widget)
        self.notebook_sidebar = PDFNotebookSidebar(self.state, None, self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.notebook_sidebar)

        # Set central widget
        self.setCentralWidget(self.central_container)

        # Show welcome placeholder initially
        self.show_welcome_message()

        # Enable drag and drop functionality
        self.setAcceptDrops(True)
        self.tab_widget.installEventFilter(self)

    def connect_signals(self) -> None:
        """
        Connect signals from DocumentState, Toolbar, SearchBar, Canvas and Notebook.
        """
        # Connect toolbar actions
        self.toolbar.open_action.triggered.connect(self.open_pdf)
        self.toolbar.extract_action.triggered.connect(self.extract_text)

        # Connect State signals (Theme only since pages/zoom are dynamic per-tab now)
        self.state.theme_changed.connect(self.apply_theme)

        # Connect Search Bar signals
        self.search_bar.search_requested.connect(self.perform_search)
        self.search_bar.search_cleared.connect(self.clear_search_highlights)
        self.search_bar.close_requested.connect(self.hide_search_bar)

        # Connect Notebook Sidebar signals
        self.notebook_sidebar.note_selected.connect(self.on_note_selected)
        self.notebook_sidebar.note_deleted.connect(self.on_note_deleted)

        # Connect toolbar outline and notebook toggles
        self.toolbar.outline_action.triggered.connect(self.toggle_outline)
        self.toolbar.notebook_action.triggered.connect(self.toggle_notebook)

        # Connect dock widget visibility changes back to toolbar action check states
        self.sidebar.visibilityChanged.connect(self.toolbar.outline_action.setChecked)
        self.notebook_sidebar.visibilityChanged.connect(self.toolbar.notebook_action.setChecked)
        
        # Connect Tab Widget signals
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)

    def setup_shortcuts(self) -> None:
        """
        Setup keyboard shortcuts for fast navigation.
        """
        # Page Navigation Shortcuts (delegated to active tab)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.prev_page)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.next_page)
        
        # Search Shortcuts
        QShortcut(QKeySequence("Ctrl+F"), self, self.toggle_search_bar)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.hide_search_bar)

    def prev_page(self) -> None:
        if self.active_tab:
            self.active_tab.state.prev_page()

    def next_page(self) -> None:
        if self.active_tab:
            self.active_tab.state.next_page()

    def on_tab_changed(self, index: int) -> None:
        """
        Sync toolbar and sidebars when active tab changes.
        """
        if index < 0 or index >= self.tab_widget.count():
            self.active_tab = None
            self.toolbar.set_active_state(None)
            self.sidebar.clear_outline()
            self.notebook_sidebar.clear_notes_list()
            self.show_welcome_message()
            return

        # Fetch the selected PDFTab
        tab = self.tab_widget.widget(index)
        if not isinstance(tab, PDFTab):
            return

        self.active_tab = tab
        self.welcome_widget.setVisible(False)
        self.tab_widget.setVisible(True)

        # Synchronize Toolbar with new tab state
        self.toolbar.set_active_state(tab.state)
        
        # Sync Sidebar Table of Contents (Outline)
        # Disconnect old state signals first
        if self.sidebar.state:
            try:
                self.sidebar.state.document_loaded.disconnect(self.sidebar.load_outline)
                self.sidebar.state.document_closed.disconnect(self.sidebar.clear_outline)
            except TypeError:
                pass
                
        self.sidebar.pdf_engine = tab.pdf_engine
        self.sidebar.state = tab.state
        
        self.sidebar.state.document_loaded.connect(self.sidebar.load_outline)
        self.sidebar.state.document_closed.connect(self.sidebar.clear_outline)
        self.sidebar.load_outline()
        
        # Sync Notebook Sidebar
        # Disconnect old state signals first
        if self.notebook_sidebar.state:
            try:
                self.notebook_sidebar.state.document_loaded.disconnect(self.notebook_sidebar.load_notes_list)
                self.notebook_sidebar.state.document_closed.disconnect(self.notebook_sidebar.clear_notes_list)
            except TypeError:
                pass
                
        self.notebook_sidebar.notes_manager = tab.notes_manager
        self.notebook_sidebar.state = tab.state
        
        self.notebook_sidebar.state.document_loaded.connect(self.notebook_sidebar.load_notes_list)
        self.notebook_sidebar.state.document_closed.connect(self.notebook_sidebar.clear_notes_list)
        self.notebook_sidebar.load_notes_list()
        
        # Update Window Title
        file_name = os.path.basename(tab.file_path)
        self.setWindowTitle(f"Kailash PDF Reader - {file_name}")
        
        # Sync dark/light theme state
        tab.state.theme = self.state.theme
        tab.apply_theme_to_canvases(self.state.theme)

    def close_tab(self, index: int) -> None:
        """
        Close the tab at the given index.
        """
        tab = self.tab_widget.widget(index)
        if isinstance(tab, PDFTab):
            tab.close_tab()
            self.tab_widget.removeTab(index)
            tab.deleteLater()
            
        if self.tab_widget.count() == 0:
            self.show_welcome_message()

    def close_tab_by_widget(self, tab: QWidget) -> None:
        """
        Close the tab corresponding to the given tab widget.
        """
        idx = self.tab_widget.indexOf(tab)
        if idx != -1:
            self.close_tab(idx)

    def apply_theme(self, theme: str) -> None:
        """
        Apply the selected QSS stylesheet and sync theme to all opened tabs.
        """
        app = QApplication.instance()
        if app:
            if theme == 'light':
                app.setStyleSheet(LIGHT_STYLE)
            else:
                app.setStyleSheet(DARK_STYLE)
        
        # Apply theme stylesheet on welcome screen
        self.show_welcome_message()
        if self.tab_widget.count() > 0:
            self.welcome_widget.setVisible(False)
            self.tab_widget.setVisible(True)
            
        # Update styling of all opened tabs
        for idx in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(idx)
            if isinstance(tab, PDFTab):
                tab.state.theme = theme
                tab.apply_theme_to_canvases(theme)

    def show_welcome_message(self) -> None:
        """
        Display the startup screen with instruction.
        """
        self.welcome_widget.setVisible(True)
        self.tab_widget.setVisible(False)
        self.welcome_label.setText("Welcome to Kailash PDF Reader! Click the Open icon on the toolbar to start.")
        if self.state.theme == 'light':
            self.welcome_label.setStyleSheet("color: #555555; font-size: 16px; background-color: #f0f0f2; padding: 20px; border-radius: 10px;")
        else:
            self.welcome_label.setStyleSheet("color: #aaaaaa; font-size: 16px; background-color: #121212; padding: 20px; border-radius: 10px;")
        self.welcome_label.adjustSize()
        self.setWindowTitle("Kailash PDF Reader")

    def open_pdf(self) -> None:
        """
        Open a file dialog to select and load a PDF file in a new tab.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF File",
            "",
            "PDF Files (*.pdf)"
        )
        
        if file_path:
            self.load_pdf_from_path(file_path)

    def load_pdf_from_path(self, file_path: str) -> None:
        """
        Load a PDF document into a new tab.
        """
        # Check if this file is already open in one of the tabs
        for idx in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(idx)
            if isinstance(tab, PDFTab) and tab.file_path == file_path:
                self.tab_widget.setCurrentIndex(idx)
                return

        # Create new PDFTab
        tab = PDFTab(file_path, self, self)
        
        # Load PDF inside tab
        if tab.load_pdf():
            file_name = os.path.basename(file_path)
            new_tab_idx = self.tab_widget.addTab(tab, file_name)
            
            # Create custom close button to override default QTabBar button which gets hidden by custom QSS styles.
            close_btn = QToolButton()
            close_btn.setText("×")
            close_btn.setObjectName("TabCloseButton")
            close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            close_btn.clicked.connect(lambda: self.close_tab_by_widget(tab))
            self.tab_widget.tabBar().setTabButton(new_tab_idx, QTabBar.ButtonPosition.RightSide, close_btn)
            
            self.tab_widget.setCurrentIndex(new_tab_idx)
            
            # Sync global theme to local tab state
            tab.state.theme = self.state.theme
            tab.apply_theme_to_canvases(self.state.theme)
            
            self.welcome_widget.setVisible(False)
            self.tab_widget.setVisible(True)
        else:
            QMessageBox.warning(self, "Load Failed", f"Failed to load PDF: {file_path}")
            tab.deleteLater()

    def extract_text(self) -> None:
        """
        Export all active PDF text to a .txt file for AI consumption (RAG/LLM).
        """
        if not self.active_tab or not self.active_tab.state.is_loaded:
            return
            
        pdf_path = self.active_tab.file_path
        pdf_dir = os.path.dirname(pdf_path)
        pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
        suggested_filename = os.path.join(pdf_dir, f"{pdf_name}_extracted.txt")
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Extracted Text",
            suggested_filename,
            "Text Files (*.txt)"
        )
        
        if file_path:
            # Construct a TextExtractor for the active engine
            from core.text_extractor import TextExtractor
            extractor = TextExtractor(self.active_tab.pdf_engine)
            success = extractor.extract_to_file(file_path)
            if success:
                QMessageBox.information(
                    self, 
                    "Extraction Successful", 
                    f"All text has been successfully extracted and saved to:\n\n{file_path}"
                )
            else:
                QMessageBox.warning(
                    self, 
                    "Extraction Failed", 
                    "An error occurred while saving the extracted text."
                )

    # Highlight and Notebook additions
    def add_highlight(self, page: int, text: str, rects: list, color: str) -> None:
        """
        Add a colored text highlight annotation to the active tab.
        """
        if not self.active_tab:
            return
        self.active_tab.notes_manager.add_note(page, text, "", rects, color)
        self.active_tab.render_all_visible_pages()
        self.notebook_sidebar.load_notes_list()

    def add_note(self, page: int, text: str, rects: list) -> None:
        """
        Add a text note with a highlight annotation to the active tab.
        """
        if not self.active_tab:
            return
        preview_text = text if len(text) <= 50 else f"{text[:50]}..."
        if not text:
            preview_text = "[Image / Area Selection]"
            
        note_text, ok = QInputDialog.getMultiLineText(
            self,
            "Add Note / Thêm ghi chú",
            f"Add note for selected area:\n\"{preview_text}\"\n\nEnter note content:",
            ""
        )
        
        if ok and note_text.strip():
            self.active_tab.notes_manager.add_note(page, text, note_text.strip(), rects, "yellow")
            self.active_tab.render_all_visible_pages()
            self.notebook_sidebar.load_notes_list()

    def on_note_selected(self, note: dict) -> None:
        """
        Jump to page and focus scroll area on the note text location.
        """
        if not self.active_tab:
            return
        self.active_tab.on_note_selected(note)

    def on_note_deleted(self) -> None:
        """
        Refresh active canvases when a note is removed.
        """
        if self.active_tab:
            self.active_tab.on_note_deleted()

    # Search Logic
    def toggle_search_bar(self) -> None:
        """
        Toggle visibility of the search bar.
        """
        if not self.active_tab or not self.active_tab.state.is_loaded:
            return
        
        is_visible = self.search_container.isVisible()
        self.search_container.setVisible(not is_visible)
        if not is_visible:
            self.search_bar.focus_input()
        else:
            self.clear_search_highlights()

    def hide_search_bar(self) -> None:
        """
        Hide the search bar.
        """
        self.search_container.setVisible(False)
        self.clear_search_highlights()

    def clear_search_highlights(self) -> None:
        """
        Clear all search highlights and redraw page on the active tab.
        """
        if self.active_tab:
            self.active_tab.search_term = ""
            self.active_tab.search_results = []
            self.active_tab.current_match_index = -1
            self.active_tab.render_all_visible_pages()

    def perform_search(self, text: str, forward: bool) -> None:
        """
        Execute document search on the active tab.
        """
        if not self.active_tab or not self.active_tab.state.is_loaded or not text:
            return

        tab = self.active_tab
        if text != tab.search_term:
            tab.search_term = text
            results = tab.pdf_engine.search_text_on_page(tab.state.current_page, text)
            
            if results:
                tab.search_results = results
                tab.current_match_index = 0
                tab.render_current_page()
                self.search_bar.set_result_status(1, len(results))
            else:
                self.scan_other_pages_for_search(text, tab.state.current_page, forward)
        else:
            if not tab.search_results:
                self.scan_other_pages_for_search(text, tab.state.current_page, forward)
                return

            if forward:
                tab.current_match_index += 1
                if tab.current_match_index >= len(tab.search_results):
                    self.scan_other_pages_for_search(text, tab.state.current_page, forward)
                else:
                    tab.render_current_page()
                    self.search_bar.set_result_status(tab.current_match_index + 1, len(tab.search_results))
            else:
                tab.current_match_index -= 1
                if tab.current_match_index < 0:
                    self.scan_other_pages_for_search(text, tab.state.current_page, forward)
                else:
                    tab.render_current_page()
                    self.search_bar.set_result_status(tab.current_match_index + 1, len(tab.search_results))

    def scan_other_pages_for_search(self, text: str, start_page: int, forward: bool) -> None:
        """
        Iterate through other pages to find matches and jump on the active tab.
        """
        if not self.active_tab:
            return
            
        tab = self.active_tab
        total = tab.state.total_pages
        if forward:
            pages_to_check = list(range(start_page + 1, total)) + list(range(0, start_page + 1))
        else:
            pages_to_check = list(range(start_page - 1, -1, -1)) + list(range(total - 1, start_page - 1, -1))

        for page_idx in pages_to_check:
            matches = tab.pdf_engine.search_text_on_page(page_idx, text)
            if matches:
                tab.search_results = matches
                tab.current_match_index = 0 if forward else len(matches) - 1
                tab.state.current_page = page_idx
                self.search_bar.set_result_status(tab.current_match_index + 1, len(matches))
                return

        tab.search_results = []
        tab.current_match_index = -1
        tab.render_current_page()
        self.search_bar.set_result_status(0, 0)

    # Wheel Zoom event
    def wheelEvent(self, event) -> None:
        """
        Intercept wheel events for Zoom (Ctrl + Wheel).
        """
        if self.active_tab and event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.active_tab.state.zoom_in(0.05)
            else:
                self.active_tab.state.zoom_out(0.05)
            event.accept()
        else:
            super().wheelEvent(event)

    def on_fit_mode_changed(self, mode: str) -> None:
        """
        Triggered when fit mode changes.
        """
        if self.active_tab:
            self.active_tab.state.fit_mode = mode

    def resizeEvent(self, event) -> None:
        """
        Handle window resizing to recalculate Zoom on Fit modes.
        """
        super().resizeEvent(event)
        if self.active_tab and self.active_tab.state.is_loaded and self.active_tab.state.fit_mode != 'none':
            self.active_tab.calculate_and_apply_fit_zoom()

    def eventFilter(self, watched, event) -> bool:
        """
        Filter events to handle Drag and Drop on viewport and canvas,
        as well as page zooming.
        """
        if event.type() == QEvent.Type.Wheel:
            if not self.active_tab:
                return False
            # Handle Ctrl + Wheel for zooming
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                delta = event.angleDelta().y()
                if delta > 0:
                    self.active_tab.state.zoom_in(0.05)
                else:
                    self.active_tab.state.zoom_out(0.05)
                return True
            # Let the default scroll area scroll continuously
            return False

        if event.type() == QEvent.Type.DragEnter:
            if event.mimeData().hasUrls():
                for url in event.mimeData().urls():
                    if url.toLocalFile().lower().endswith('.pdf'):
                        event.acceptProposedAction()
                        return True
            return False
            
        elif event.type() == QEvent.Type.DragMove:
            if event.mimeData().hasUrls():
                for url in event.mimeData().urls():
                    if url.toLocalFile().lower().endswith('.pdf'):
                        event.acceptProposedAction()
                        return True
            return False
            
        elif event.type() == QEvent.Type.Drop:
            if event.mimeData().hasUrls():
                for url in event.mimeData().urls():
                    file_path = url.toLocalFile()
                    if file_path.lower().endswith('.pdf'):
                        self.load_pdf_from_path(file_path)
                        event.acceptProposedAction()
                        return True
            return False
            
        return False

    def dragEnterEvent(self, event) -> None:
        """
        Accept drag-enter events if they contain at least one local PDF file.
        """
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.pdf'):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event) -> None:
        """
        Open the first PDF file dropped onto the application window.
        """
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith('.pdf'):
                    self.load_pdf_from_path(file_path)
                    event.acceptProposedAction()
                    return

    def toggle_outline(self, checked: bool) -> None:
        """
        Show or hide the document outline sidebar.
        """
        self.sidebar.setVisible(checked)

    def toggle_notebook(self, checked: bool) -> None:
        """
        Show or hide the notebook sidebar.
        """
        self.notebook_sidebar.setVisible(checked)

    def closeEvent(self, event) -> None:
        """
        Cleanups.
        """
        for idx in range(self.tab_widget.count()):
            tab = self.tab_widget.widget(idx)
            if isinstance(tab, PDFTab):
                tab.close_tab()
        self.state.close_document()
        event.accept()

