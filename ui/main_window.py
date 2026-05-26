import os
from PyQt6.QtWidgets import QMainWindow, QFileDialog, QScrollArea, QLabel, QApplication, QWidget, QVBoxLayout, QMessageBox, QInputDialog
from PyQt6.QtCore import Qt, QRectF, QEvent
from PyQt6.QtGui import QPixmap, QShortcut, QKeySequence, QPainter, QColor, QIcon, QDragEnterEvent, QDragMoveEvent, QDropEvent
from core.pdf_engine import PDFEngine
from core.state import DocumentState
from core.text_extractor import TextExtractor
from core.notes_manager import NotesManager
from ui.toolbar import PDFToolBar
from ui.sidebar import PDFSidebar
from ui.search_bar import PDFSearchBar
from ui.canvas import PDFCanvas
from ui.notebook_sidebar import PDFNotebookSidebar
from ui.stylesheets import LIGHT_STYLE, DARK_STYLE

class MainWindow(QMainWindow):
    def __init__(self):
        """
        Initialize the Main Window.
        """
        super().__init__()
        # Core components
        self.pdf_engine = PDFEngine()
        self.state = DocumentState()
        self.text_extractor = TextExtractor(self.pdf_engine)
        self.notes_manager = NotesManager()
        
        # Search state variables
        self.search_term = ""
        self.search_results = []
        self.current_match_index = -1
        
        self.init_ui()
        self.connect_signals()
        self.setup_shortcuts()
        
        # Apply initial theme (Light Mode)
        self.apply_theme(self.state.theme)

    def init_ui(self) -> None:
        """
        Setup the UI components.
        """
        self.setWindowTitle("Premium PDF Reader")
        self.resize(1200, 800)

        # Set window and Dock icon using the generated logo
        if os.path.exists("logo.png"):
            self.setWindowIcon(QIcon("logo.png"))

        # 1. Custom PDF Toolbar
        self.toolbar = PDFToolBar(self.state, self)
        self.addToolBar(self.toolbar)

        # 2. Main Central Container (to lay search bar on top of scroll area)
        central_container = QWidget()
        container_layout = QVBoxLayout(central_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        # Create Search Bar inside a styled container for QSS styling
        self.search_container = QWidget()
        self.search_container.setObjectName("SearchBarContainer")
        search_layout = QVBoxLayout(self.search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_bar = PDFSearchBar(self)
        search_layout.addWidget(self.search_bar)
        
        # Hide search bar by default
        self.search_container.setVisible(False)
        container_layout.addWidget(self.search_container)

        # Create ScrollArea to display pages
        self.scroll_area = QScrollArea()
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidgetResizable(False)

        # Create custom PDFCanvas (supporting selection and context menus)
        self.canvas = PDFCanvas(self.state, self.pdf_engine, self)
        self.canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.canvas)
        container_layout.addWidget(self.scroll_area)
        
        self.setCentralWidget(central_container)

        # 3. Create PDF Sidebar - Document Outline (Left Dock Widget)
        self.sidebar = PDFSidebar(self.state, self.pdf_engine, self)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        # 4. Create PDF Notebook Sidebar - Highlights & Notes (Right Dock Widget)
        self.notebook_sidebar = PDFNotebookSidebar(self.state, self.notes_manager, self)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.notebook_sidebar)

        # Show welcome placeholder
        self.show_welcome_message()

        # Enable drag and drop functionality
        self.setAcceptDrops(True)
        
        # Install event filter to capture drag and drop on scroll area and canvas
        self.scroll_area.viewport().installEventFilter(self)
        self.canvas.installEventFilter(self)
        self.scroll_area.setAcceptDrops(True)

    def connect_signals(self) -> None:
        """
        Connect signals from DocumentState, Toolbar, SearchBar, Canvas and Notebook.
        """
        # Connect toolbar actions
        self.toolbar.open_action.triggered.connect(self.open_pdf)
        self.toolbar.extract_action.triggered.connect(self.extract_text)

        # Connect State signals
        self.state.page_changed.connect(self.on_page_changed)
        self.state.zoom_changed.connect(self.on_zoom_changed)
        self.state.fit_mode_changed.connect(self.on_fit_mode_changed)
        self.state.theme_changed.connect(self.apply_theme)
        self.state.document_closed.connect(self.show_welcome_message)

        # Connect Search Bar signals
        self.search_bar.search_requested.connect(self.perform_search)
        self.search_bar.search_cleared.connect(self.clear_search_highlights)
        self.search_bar.close_requested.connect(self.hide_search_bar)

        # Connect PDF Canvas selection signals
        self.canvas.text_highlighted.connect(self.add_highlight)
        self.canvas.text_note_added.connect(self.add_note)

        # Connect Notebook Sidebar signals
        self.notebook_sidebar.note_selected.connect(self.on_note_selected)
        self.notebook_sidebar.note_deleted.connect(self.on_note_deleted)

    def setup_shortcuts(self) -> None:
        """
        Setup keyboard shortcuts for fast navigation.
        """
        # Page Navigation Shortcuts
        QShortcut(QKeySequence(Qt.Key.Key_Left), self, self.state.prev_page)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self, self.state.next_page)
        
        # Search Shortcuts
        QShortcut(QKeySequence("Ctrl+F"), self, self.toggle_search_bar)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self, self.hide_search_bar)

    def apply_theme(self, theme: str) -> None:
        """
        Apply the selected QSS stylesheet.
        """
        app = QApplication.instance()
        if app:
            if theme == 'light':
                app.setStyleSheet(LIGHT_STYLE)
            else:
                app.setStyleSheet(DARK_STYLE)
        
        # Recolor canvas placeholder if document is not loaded
        if not self.state.is_loaded:
            self.show_welcome_message()

    def show_welcome_message(self) -> None:
        """
        Display the startup screen with instruction.
        """
        self.canvas.setText("Welcome! Click the Open icon on the toolbar, or drag and drop a PDF file.")
        if self.state.theme == 'light':
            self.canvas.setStyleSheet("color: #555555; font-size: 16px; background-color: #f0f0f2; padding: 20px; border-radius: 10px;")
        else:
            self.canvas.setStyleSheet("color: #aaaaaa; font-size: 16px; background-color: #121212; padding: 20px; border-radius: 10px;")
        self.canvas.adjustSize()

    def open_pdf(self) -> None:
        """
        Open a file dialog to select and load a PDF file.
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
        Load a PDF document from the given local file path.
        """
        self.pdf_engine.close_document()
        # Clear search bar input on new document
        self.search_bar.search_input.clear()
        self.clear_search_state()
        
        # Load local notes associated with the PDF file
        self.notes_manager.set_pdf_path(file_path)
        
        success = self.pdf_engine.load_document(file_path)
        
        if success:
            # Update window title
            file_name = os.path.basename(file_path)
            self.setWindowTitle(f"Premium PDF Reader - {file_name}")
            
            # Load state (this triggers state loaded event)
            self.state.load_document(self.pdf_engine.get_page_count())
            
            # Populate notes list in the notebook sidebar
            self.notebook_sidebar.load_notes_list()
            
            # Apply Fit or Render first page
            if self.state.fit_mode != 'none':
                old_zoom = self.state.zoom_level
                self.calculate_and_apply_fit_zoom()
                if old_zoom == self.state.zoom_level:
                    self.render_current_page()
            else:
                self.render_current_page()
        else:
            self.canvas.setText("Failed to load PDF. Please select a valid file.")
            self.canvas.setStyleSheet("color: #ff3333; font-size: 16px; background-color: #121212; padding: 20px;")
            self.canvas.adjustSize()

    def extract_text(self) -> None:
        """
        Export all PDF text to a .txt file for AI consumption (RAG/LLM).
        """
        if not self.state.is_loaded:
            return
            
        pdf_path = self.pdf_engine.current_file_path
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
            success = self.text_extractor.extract_to_file(file_path)
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
        Add a colored text highlight annotation.
        """
        self.notes_manager.add_note(page, text, "", rects, color)
        self.render_current_page()
        self.notebook_sidebar.load_notes_list()

    def add_note(self, page: int, text: str, rects: list) -> None:
        """
        Add a text note with a highlight annotation.
        """
        preview_text = text if len(text) <= 50 else f"{text[:50]}..."
        note_text, ok = QInputDialog.getMultiLineText(
            self,
            "Add Note / Thêm ghi chú",
            f"Add note for selected text:\n\"{preview_text}\"\n\nEnter note content:",
            ""
        )
        
        if ok and note_text.strip():
            # Save notes with yellow highlight as default visual marker
            self.notes_manager.add_note(page, text, note_text.strip(), rects, "yellow")
            self.render_current_page()
            self.notebook_sidebar.load_notes_list()

    def on_note_selected(self, note: dict) -> None:
        """
        Jump to page and focus scroll area on the note text location.
        """
        # Jump page
        self.state.current_page = note["page"]
        
        # Center viewport on note location
        if note.get("rects"):
            r = note["rects"][0]
            # Calculate zoomed bounding rectangle
            scaled_rect = QRectF(
                r[0] * self.state.zoom_level,
                r[1] * self.state.zoom_level,
                (r[2] - r[0]) * self.state.zoom_level,
                (r[3] - r[1]) * self.state.zoom_level
            )
            self.scroll_to_rect(scaled_rect)

    def on_note_deleted(self) -> None:
        """
        Refresh canvas when a note is removed.
        """
        self.render_current_page()

    def render_current_page(self) -> None:
        """
        Fetch the page pixmap from PDFEngine and render on canvas.
        Highlights search results and user note highlights.
        """
        if not self.state.is_loaded:
            return

        # Fetch user highlights for current page from notes manager
        db_highlights = self.notes_manager.get_notes_for_page(self.state.current_page)

        # Fetch rendered QPixmap containing all highlights
        pixmap = self.pdf_engine.render_page(
            self.state.current_page,
            self.state.zoom_level,
            highlight_rects=self.search_results,
            db_highlights=db_highlights
        )
        
        # If there are search results, draw the ACTIVE search match in orange
        if not pixmap.isNull() and self.search_results and 0 <= self.current_match_index < len(self.search_results):
            active_rect = self.search_results[self.current_match_index]
            
            painter = QPainter(pixmap)
            painter.setBrush(QColor(255, 128, 0, 140))
            painter.setPen(QColor(255, 64, 0))
            
            scaled_rect = QRectF(
                active_rect.x0 * self.state.zoom_level,
                active_rect.y0 * self.state.zoom_level,
                (active_rect.x1 - active_rect.x0) * self.state.zoom_level,
                (active_rect.y1 - active_rect.y0) * self.state.zoom_level
            )
            painter.drawRect(scaled_rect)
            painter.end()
            
            self.scroll_to_rect(scaled_rect)

        if not pixmap.isNull():
            self.canvas.setPixmap(pixmap)
            self.canvas.setStyleSheet("background-color: transparent;")
            self.canvas.adjustSize()
        else:
            self.canvas.setText("Error rendering page.")
            self.canvas.setStyleSheet("color: #ff3333; font-size: 16px;")
            self.canvas.adjustSize()

    def scroll_to_rect(self, rect: QRectF) -> None:
        """
        Auto-scroll the scrollbars to center the target rectangle.
        """
        h_bar = self.scroll_area.horizontalScrollBar()
        vp_w = self.scroll_area.viewport().width()
        target_h = int(rect.center().x() - vp_w / 2)
        h_bar.setValue(target_h)

        v_bar = self.scroll_area.verticalScrollBar()
        vp_h = self.scroll_area.viewport().height()
        target_v = int(rect.center().y() - vp_h / 2)
        v_bar.setValue(target_v)

    def calculate_and_apply_fit_zoom(self) -> None:
        """
        Calculate and apply the fit-to-window zoom level.
        """
        if not self.state.is_loaded or self.state.fit_mode == 'none':
            return
            
        page_w, page_h = self.pdf_engine.get_page_size(self.state.current_page)
        if page_w <= 0 or page_h <= 0:
            return

        vp_w = self.scroll_area.viewport().width()
        vp_h = self.scroll_area.viewport().height()
        margin = 20

        if self.state.fit_mode == 'width':
            target_zoom = (vp_w - margin) / page_w
        elif self.state.fit_mode == 'height':
            target_zoom = (vp_h - margin) / page_h
        else:
            return

        self.state.zoom_level = target_zoom

    # Search Logic
    def toggle_search_bar(self) -> None:
        """
        Toggle visibility of the search bar.
        """
        if not self.state.is_loaded:
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

    def clear_search_state(self) -> None:
        """
        Reset search data.
        """
        self.search_term = ""
        self.search_results = []
        self.current_match_index = -1

    def clear_search_highlights(self) -> None:
        """
        Clear all search highlights and redraw page.
        """
        self.clear_search_state()
        self.render_current_page()

    def perform_search(self, text: str, forward: bool) -> None:
        """
        Execute document search.
        Handles text search across current page or jumps to other pages.
        """
        if not self.state.is_loaded or not text:
            return

        if text != self.search_term:
            self.search_term = text
            results = self.pdf_engine.search_text_on_page(self.state.current_page, text)
            
            if results:
                self.search_results = results
                self.current_match_index = 0
                self.render_current_page()
                self.search_bar.set_result_status(1, len(results))
            else:
                self.scan_other_pages_for_search(text, self.state.current_page, forward)
        else:
            if not self.search_results:
                self.scan_other_pages_for_search(text, self.state.current_page, forward)
                return

            if forward:
                self.current_match_index += 1
                if self.current_match_index >= len(self.search_results):
                    self.scan_other_pages_for_search(text, self.state.current_page, forward)
                else:
                    self.render_current_page()
                    self.search_bar.set_result_status(self.current_match_index + 1, len(self.search_results))
            else:
                self.current_match_index -= 1
                if self.current_match_index < 0:
                    self.scan_other_pages_for_search(text, self.state.current_page, forward)
                else:
                    self.render_current_page()
                    self.search_bar.set_result_status(self.current_match_index + 1, len(self.search_results))

    def scan_other_pages_for_search(self, text: str, start_page: int, forward: bool) -> None:
        """
        Iterate through other pages to find matches and jump.
        """
        total = self.state.total_pages
        if forward:
            pages_to_check = list(range(start_page + 1, total)) + list(range(0, start_page + 1))
        else:
            pages_to_check = list(range(start_page - 1, -1, -1)) + list(range(total - 1, start_page - 1, -1))

        for page_idx in pages_to_check:
            matches = self.pdf_engine.search_text_on_page(page_idx, text)
            if matches:
                self.search_results = matches
                self.current_match_index = 0 if forward else len(matches) - 1
                self.state.current_page = page_idx
                self.search_bar.set_result_status(self.current_match_index + 1, len(matches))
                return

        self.search_results = []
        self.current_match_index = -1
        self.render_current_page()
        self.search_bar.set_result_status(0, 0)

    # Wheel Zoom event
    def wheelEvent(self, event) -> None:
        """
        Intercept wheel events for Zoom (Ctrl + Wheel).
        """
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.state.zoom_in(0.05)
            else:
                self.state.zoom_out(0.05)
            event.accept()
        else:
            super().wheelEvent(event)

    # Slots
    def on_page_changed(self, page_index: int) -> None:
        """
        Triggered when current page changes.
        """
        if self.search_term:
            results = self.pdf_engine.search_text_on_page(page_index, self.search_term)
            self.search_results = results
            if results:
                if self.current_match_index < 0 or self.current_match_index >= len(results):
                    self.current_match_index = 0
                self.search_bar.set_result_status(self.current_match_index + 1, len(results))
            else:
                self.current_match_index = -1
                self.search_bar.set_result_status(0, 0)
        else:
            self.clear_search_state()
            
        if self.state.fit_mode != 'none':
            old_zoom = self.state.zoom_level
            self.calculate_and_apply_fit_zoom()
            if old_zoom == self.state.zoom_level:
                self.render_current_page()
        else:
            self.render_current_page()

    def on_zoom_changed(self) -> None:
        """
        Triggered when zoom level changes.
        """
        self.render_current_page()

    def on_fit_mode_changed(self, mode: str) -> None:
        """
        Triggered when fit mode changes.
        """
        if mode != 'none':
            old_zoom = self.state.zoom_level
            self.calculate_and_apply_fit_zoom()
            if old_zoom == self.state.zoom_level:
                self.render_current_page()

    def resizeEvent(self, event) -> None:
        """
        Handle window resizing to recalculate Zoom on Fit modes.
        """
        super().resizeEvent(event)
        if self.state.is_loaded and self.state.fit_mode != 'none':
            self.calculate_and_apply_fit_zoom()

    def eventFilter(self, watched, event) -> bool:
        """
        Filter events to handle Drag and Drop on viewport and canvas.
        """
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
            
        return super().eventFilter(watched, event)

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

    def closeEvent(self, event) -> None:
        """
        Cleanups.
        """
        self.pdf_engine.close_document()
        self.state.close_document()
        event.accept()
