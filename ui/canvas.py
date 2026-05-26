import fitz
from PyQt6.QtWidgets import QLabel, QMenu, QApplication
from PyQt6.QtCore import Qt, QRect, pyqtSignal, QPoint
from PyQt6.QtGui import QPainter, QColor, QPen
from core.state import DocumentState
from core.pdf_engine import PDFEngine

class PDFCanvas(QLabel):
    # Signals to communicate selection actions to MainWindow
    # (page_index, selected_text, rects, color_name)
    text_highlighted = pyqtSignal(int, str, list, str)
    # (page_index, selected_text, rects)
    text_note_added = pyqtSignal(int, str, list)

    def __init__(self, page_index: int, state: DocumentState, pdf_engine: PDFEngine, parent=None):
        """
        Initialize the PDF Canvas for a specific page.
        """
        super().__init__(parent)
        self.page_index = page_index
        self.state = state
        self.pdf_engine = pdf_engine
        
        # Mouse selection state
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        
        # Selected text data
        self.selected_text = ""
        self.selected_rects = []
        
        # Configure interaction options
        self.setMouseTracking(True)

    def mousePressEvent(self, event) -> None:
        """
        Handle mouse click. Start text selection.
        """
        if not self.state.is_loaded:
            return
            
        if event.button() == Qt.MouseButton.LeftButton:
            # Use event.pos() for compatibility and exact integer coordinates
            self.start_pos = event.pos()
            self.end_pos = self.start_pos
            self.is_selecting = True
            
            # Clear previous selection data
            self.selected_text = ""
            self.selected_rects = []
            self.update()

    def mouseMoveEvent(self, event) -> None:
        """
        Handle mouse movement. Update selection box or change cursor shape on hover.
        """
        if self.is_selecting:
            self.end_pos = event.pos()
            self.update()
        else:
            # Change cursor to I-beam if hovering over text, otherwise default arrow
            if not self.state.is_loaded:
                return
                
            zoom = self.state.zoom_level
            px = event.pos().x() / zoom
            py = event.pos().y() / zoom
            point = fitz.Point(px, py)
            
            # Fetch words on the current page
            words = self.pdf_engine.get_text_words(self.page_index)
            
            hovering_over_text = False
            for w in words:
                word_rect = fitz.Rect(w[0], w[1], w[2], w[3])
                if word_rect.contains(point):
                    hovering_over_text = True
                    break
                    
            if hovering_over_text:
                self.setCursor(Qt.CursorShape.IBeamCursor)
            else:
                self.setCursor(Qt.CursorShape.ArrowCursor)

    def mouseReleaseEvent(self, event) -> None:
        """
        Handle mouse release. Finish selection and show context menu.
        """
        if self.is_selecting and event.button() == Qt.MouseButton.LeftButton:
            self.is_selecting = False
            
            if not self.start_pos or not self.end_pos:
                self.update()
                return

            # Compute drag selection box
            selection_rect = QRect(self.start_pos, self.end_pos).normalized()
            
            # If the drag is too small, consider it a simple click and discard selection
            if selection_rect.width() < 6 or selection_rect.height() < 6:
                self.start_pos = None
                self.end_pos = None
                self.update()
                return
                
            # Perform text extraction in the selected area
            self.extract_selected_text(selection_rect)
            
            # Show context menu at mouse release position (always show to improve UX)
            self.show_context_menu(event.globalPosition().toPoint())

    def extract_selected_text(self, selection_rect: QRect) -> None:
        """
        Map screen coordinates to original PDF coordinates and find contained words.
        """
        zoom = self.state.zoom_level
        
        # Convert selection coordinates back to original PDF units (72 dpi)
        rx0 = selection_rect.left() / zoom
        ry0 = selection_rect.top() / zoom
        rx1 = selection_rect.right() / zoom
        ry1 = selection_rect.bottom() / zoom
        
        pdf_sel_rect = fitz.Rect(rx0, ry0, rx1, ry1)
        
        # Get all words on the current page
        words = self.pdf_engine.get_text_words(self.page_index)
        
        selected_words = []
        for w in words:
            word_rect = fitz.Rect(w[0], w[1], w[2], w[3])
            # Check overlap using intersection operator &
            intersect = pdf_sel_rect & word_rect
            if not intersect.is_empty:
                if pdf_sel_rect.contains(word_rect) or intersect.get_area() > word_rect.get_area() * 0.3:
                    selected_words.append(w)
                    
        if not selected_words:
            # If no text found (e.g. image PDF or blank area), save the selected boundary itself
            self.selected_text = ""
            self.selected_rects = [pdf_sel_rect]
            return
            
        # Sort words naturally (by block, line, then word order)
        selected_words = sorted(selected_words, key=lambda x: (x[5], x[6], x[7]))
        
        # Reconstruct text and collect original rects
        text_parts = []
        self.selected_rects = []
        
        current_block = -1
        current_line = -1
        
        for w in selected_words:
            w_x0, w_y0, w_x1, w_y1, word_text, b_no, l_no, w_no = w
            
            # Add spaces or newlines based on reading structure
            if current_block != -1 and current_block != b_no:
                text_parts.append("\n\n")
            elif current_line != -1 and current_line != l_no:
                text_parts.append("\n")
            elif text_parts:
                text_parts.append(" ")
                
            text_parts.append(word_text)
            self.selected_rects.append(fitz.Rect(w_x0, w_y0, w_x1, w_y1))
            
            current_block = b_no
            current_line = l_no
            
        self.selected_text = "".join(text_parts).strip()

    def show_context_menu(self, global_pos: QPoint) -> None:
        """
        Display context menu at the cursor drop point.
        """
        menu = QMenu(self)
        
        # Styling Context Menu for a modern look
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #d2d2d7;
                border-radius: 8px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #0071e3;
                color: #ffffff;
            }
            QMenu::item:disabled {
                color: #8e8e93;
            }
        """)

        # Add Actions
        act_yellow = menu.addAction("🟡 Highlight Yellow")
        act_green = menu.addAction("🟢 Highlight Green")
        act_pink = menu.addAction("💗 Highlight Pink")
        menu.addSeparator()
        act_note = menu.addAction("📝 Add Note / Ghi chú")
        act_copy = menu.addAction("📋 Copy Text")
        
        # Disable Copy action if no text was selected
        if not self.selected_text:
            act_copy.setEnabled(False)
            
        menu.addSeparator()
        act_clear = menu.addAction("✖ Clear Selection")

        # Execute Menu
        action = menu.exec(global_pos)
        
        # Capture current selection before clearing state
        text = self.selected_text
        rects = self.selected_rects
        
        if action == act_yellow:
            self.text_highlighted.emit(self.page_index, text, rects, "yellow")
        elif action == act_green:
            self.text_highlighted.emit(self.page_index, text, rects, "green")
        elif action == act_pink:
            self.text_highlighted.emit(self.page_index, text, rects, "pink")
        elif action == act_note:
            self.text_note_added.emit(self.page_index, text, rects)
        elif action == act_copy and self.selected_text:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.setText(self.selected_text)
                
        # Clear the visual selection box from screen
        self.start_pos = None
        self.end_pos = None
        self.update()

    def paintEvent(self, event) -> None:
        """
        Vẽ ảnh nền trang PDF và vẽ đè selection box nếu đang kéo.
        """
        super().paintEvent(event)
        
        # Draw drag selection box on screen
        if self.is_selecting and self.start_pos and self.end_pos:
            painter = QPainter(self)
            # Semi-transparent blue fill
            painter.setBrush(QColor(0, 120, 215, 60))
            # Thin blue border
            painter.setPen(QPen(QColor(0, 120, 215), 1, Qt.PenStyle.SolidLine))
            
            rect = QRect(self.start_pos, self.end_pos).normalized()
            painter.drawRect(rect)
            painter.end()
