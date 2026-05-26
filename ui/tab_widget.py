import os
from PyQt6.QtWidgets import QWidget, QScrollArea, QVBoxLayout, QApplication
from PyQt6.QtCore import Qt, QRectF, QTimer
from PyQt6.QtGui import QPixmap, QColor, QPainter
from core.pdf_engine import PDFEngine
from core.state import DocumentState
from core.notes_manager import NotesManager
from ui.canvas import PDFCanvas

class PDFTab(QWidget):
    def __init__(self, file_path: str, main_window, parent=None):
        """
        Initialize a PDF Document Tab holding its own engine, state, notes manager, and UI.
        """
        super().__init__(parent)
        self.file_path = file_path
        self.main_window = main_window
        
        # Core engines for this tab
        self.pdf_engine = PDFEngine()
        self.state = DocumentState()
        self.notes_manager = NotesManager()
        
        # Search state for this tab
        self.search_term = ""
        self.search_results = []
        self.current_match_index = -1
        
        # Scroll & Page Transition state variables
        self.wheel_accumulator = 0
        self._scroll_to_top_after_load = False
        self._scroll_to_bottom_after_load = False
        self._is_scrolling_programmatically = False
        self._is_updating_state_from_scroll = False
        
        self.canvases = []
        
        self.init_ui()
        self.connect_signals()

    def init_ui(self) -> None:
        """
        Setup ScrollArea for this tab.
        """
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create ScrollArea to display pages
        self.scroll_area = QScrollArea()
        self.scroll_area.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidgetResizable(True)

        # Create scroll content widget
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(15, 15, 15, 15)
        self.scroll_layout.setSpacing(15)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.scroll_widget)
        
        layout.addWidget(self.scroll_area)
        
    def connect_signals(self) -> None:
        """
        Connect local state and scroll events.
        """
        self.scroll_area.verticalScrollBar().valueChanged.connect(self.on_scroll_value_changed)
        self.state.page_changed.connect(self.on_page_changed)
        self.state.zoom_changed.connect(self.on_zoom_changed)
        self.state.fit_mode_changed.connect(self.on_fit_mode_changed)

    def load_pdf(self) -> bool:
        """
        Load document and populate page canvases.
        """
        self.notes_manager.set_pdf_path(self.file_path)
        success = self.pdf_engine.load_document(self.file_path)
        if success:
            self.state.load_document(self.pdf_engine.get_page_count())
            
            # Create a canvas for each page
            for i in range(self.state.total_pages):
                canvas = PDFCanvas(i, self.state, self.pdf_engine, self.main_window)
                if self.main_window.state.theme == 'light':
                    canvas.setStyleSheet("background-color: #ffffff; border: 1px solid #d2d2d7; border-radius: 2px;")
                else:
                    canvas.setStyleSheet("background-color: #1e1e1e; border: 1px solid #3d3d3d; border-radius: 2px;")
                
                canvas.text_highlighted.connect(self.main_window.add_highlight)
                canvas.text_note_added.connect(self.main_window.add_note)
                canvas.installEventFilter(self.main_window)
                self.scroll_layout.addWidget(canvas)
                self.canvases.append(canvas)
                
            self.render_all_visible_pages()
            self.scroll_area.verticalScrollBar().setValue(0)
            return True
        return False

    def clear_canvases(self) -> None:
        """
        Remove all canvas page widgets.
        """
        for canvas in self.canvases:
            self.scroll_layout.removeWidget(canvas)
            canvas.deleteLater()
        self.canvases.clear()

    def render_page_pixmap(self, page_index: int) -> QPixmap:
        """
        Fetch pixmap with highlights overlaid.
        """
        db_highlights = self.notes_manager.get_notes_for_page(page_index)
        page_search_results = self.search_results if page_index == self.state.current_page else []
        
        pixmap = self.pdf_engine.render_page(
            page_index,
            self.state.zoom_level,
            highlight_rects=page_search_results,
            db_highlights=db_highlights
        )
        
        # Draw active search match in orange
        if not pixmap.isNull() and page_index == self.state.current_page and self.search_results and 0 <= self.current_match_index < len(self.search_results):
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
            
        return pixmap

    def render_all_visible_pages(self) -> None:
        """
        Resize canvases and lazy-render pages close to the current page.
        """
        if not self.state.is_loaded:
            return
            
        curr = self.state.current_page
        zoom = self.state.zoom_level
        
        for idx, canvas in enumerate(self.canvases):
            w, h = self.pdf_engine.get_page_size(idx)
            target_w = int(w * zoom)
            target_h = int(h * zoom)
            canvas.setFixedSize(target_w, target_h)
            
            # Lazy load pages close to current page (load window of 2 pages)
            if abs(idx - curr) <= 2:
                pixmap = self.render_page_pixmap(idx)
                if not pixmap.isNull():
                    canvas.setPixmap(pixmap)
            else:
                canvas.clear()

    def scroll_to_page(self, page_index: int) -> None:
        """
        Scroll viewport to show the top of the selected page.
        """
        if not self.state.is_loaded or page_index < 0 or page_index >= len(self.canvases):
            return
            
        canvas = self.canvases[page_index]
        self._is_scrolling_programmatically = True
        self.scroll_area.ensureWidgetVisible(canvas, xMargin=0, yMargin=10)
        
        QTimer.singleShot(150, self.reset_scroll_flag)

    def scroll_to_rect_on_page(self, page_index: int, rect: QRectF) -> None:
        """
        Center on a rectangle on a specific page canvas.
        """
        if not self.state.is_loaded or page_index < 0 or page_index >= len(self.canvases):
            return
            
        canvas = self.canvases[page_index]
        self._is_scrolling_programmatically = True
        
        canvas_x = canvas.geometry().x()
        canvas_y = canvas.geometry().y()
        
        global_rect_x = canvas_x + rect.x()
        global_rect_y = canvas_y + rect.y()
        
        h_bar = self.scroll_area.horizontalScrollBar()
        vp_w = self.scroll_area.viewport().width()
        target_h = int(global_rect_x + rect.width() / 2 - vp_w / 2)
        h_bar.setValue(target_h)
        
        v_bar = self.scroll_area.verticalScrollBar()
        vp_h = self.scroll_area.viewport().height()
        target_v = int(global_rect_y + rect.height() / 2 - vp_h / 2)
        v_bar.setValue(target_v)
        
        QTimer.singleShot(150, self.reset_scroll_flag)

    def reset_scroll_flag(self) -> None:
        self._is_scrolling_programmatically = False

    def on_scroll_value_changed(self, value: int) -> None:
        """
        Detect active visible page index based on viewport center.
        """
        if not self.state.is_loaded or not self.canvases:
            return
            
        if self._is_scrolling_programmatically:
            return
            
        viewport_height = self.scroll_area.viewport().height()
        center_y = value + viewport_height / 2
        
        current_page_candidate = 0
        min_distance = float('inf')
        
        for idx, canvas in enumerate(self.canvases):
            canvas_y = canvas.geometry().y()
            canvas_h = canvas.geometry().height()
            canvas_bottom = canvas_y + canvas_h
            
            if canvas_y <= center_y <= canvas_bottom:
                current_page_candidate = idx
                break
            else:
                dist_to_center = min(abs(canvas_y - center_y), abs(canvas_bottom - center_y))
                if dist_to_center < min_distance:
                    min_distance = dist_to_center
                    current_page_candidate = idx
                    
        if current_page_candidate != self.state.current_page:
            self._is_updating_state_from_scroll = True
            self.state.current_page = current_page_candidate
            self.render_all_visible_pages()

    def on_page_changed(self, page_index: int) -> None:
        if not self._is_updating_state_from_scroll:
            self.scroll_to_page(page_index)
            
        self._is_updating_state_from_scroll = False
        self.render_all_visible_pages()

    def on_zoom_changed(self, zoom: float) -> None:
        self.render_all_visible_pages()

    def on_fit_mode_changed(self, mode: str) -> None:
        if mode != 'none':
            self.calculate_and_apply_fit_zoom()

    def calculate_and_apply_fit_zoom(self) -> None:
        """
        Apply Fit Page logic.
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

    def apply_theme_to_canvases(self, theme: str) -> None:
        """
        Apply theme styles to canvases.
        """
        for canvas in self.canvases:
            if theme == 'light':
                canvas.setStyleSheet("background-color: #ffffff; border: 1px solid #d2d2d7; border-radius: 2px;")
            else:
                canvas.setStyleSheet("background-color: #1e1e1e; border: 1px solid #3d3d3d; border-radius: 2px;")
        self.render_all_visible_pages()

    def close_tab(self) -> None:
        """
        Clean engine and states.
        """
        self.clear_canvases()
        self.pdf_engine.close_document()
        self.state.close_document()

    def on_note_selected(self, note: dict) -> None:
        """
        Jump to page and focus scroll area on the note text location.
        """
        page = note.get("page", 0)
        self.state.current_page = page
        
        rects = note.get("rects", [])
        if rects:
            first_rect = rects[0]
            # Convert list [x0, y0, x1, y1] to QRectF
            if len(first_rect) >= 4:
                x0, y0, x1, y1 = first_rect[0], first_rect[1], first_rect[2], first_rect[3]
                zoom = self.state.zoom_level
                # Scale rect coordinates by zoom level
                qrect = QRectF(x0 * zoom, y0 * zoom, (x1 - x0) * zoom, (y1 - y0) * zoom)
                self.scroll_to_rect_on_page(page, qrect)
            else:
                self.scroll_to_page(page)
        else:
            self.scroll_to_page(page)

    def on_note_deleted(self) -> None:
        """
        Refresh page rendering because a note has been deleted.
        """
        self.render_all_visible_pages()

    def render_current_page(self) -> None:
        """
        Render the current active page canvas.
        """
        if not self.state.is_loaded:
            return
        curr = self.state.current_page
        if 0 <= curr < len(self.canvases):
            pixmap = self.render_page_pixmap(curr)
            if not pixmap.isNull():
                self.canvases[curr].setPixmap(pixmap)
