import fitz
from PyQt6.QtGui import QImage, QPixmap, QPainter, QColor
from PyQt6.QtCore import QRectF, Qt

class PDFEngine:
    def __init__(self):
        """
        Initialize the PDF Engine.
        """
        self.doc = None
        self.current_file_path = None

    def load_document(self, file_path: str) -> bool:
        """
        Load a PDF document from the given file path.
        Returns True if successful, False otherwise.
        """
        try:
            self.doc = fitz.open(file_path)
            self.current_file_path = file_path
            return True
        except Exception as e:
            print(f"Error loading PDF document: {e}")
            self.doc = None
            self.current_file_path = None
            return False

    def close_document(self) -> None:
        """
        Close the currently loaded PDF document.
        """
        if self.doc:
            self.doc.close()
            self.doc = None
            self.current_file_path = None

    def get_page_count(self) -> int:
        """
        Get the total number of pages in the loaded document.
        """
        if self.doc:
            return self.doc.page_count
        return 0

    def render_page(self, page_index: int, zoom_level: float = 1.0, highlight_rects: list = None) -> QPixmap:
        """
        Render a specific page of the PDF to a QPixmap.
        Optionally overlays highlight rectangles.
        Returns a QPixmap of the page, or a null QPixmap if failed.
        """
        if not self.doc or page_index < 0 or page_index >= self.get_page_count():
            return QPixmap()

        try:
            # Load the page
            page = self.doc.load_page(page_index)
            
            # Apply zoom matrix
            matrix = fitz.Matrix(zoom_level, zoom_level)
            
            # Render page to a PyMuPDF Pixmap
            pix = page.get_pixmap(matrix=matrix)
            
            # Convert PyMuPDF Pixmap to QImage
            # Format_RGB888 is used since get_pixmap returns 3 channels (RGB) by default
            qimage = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGB888
            )
            
            # Copy the QImage to safely detach it from PyMuPDF memory buffer
            qimage_copy = qimage.copy()
            
            # Create QPixmap
            pixmap = QPixmap.fromImage(qimage_copy)
            
            # Overlay highlights if provided
            if highlight_rects and not pixmap.isNull():
                painter = QPainter(pixmap)
                # Semi-transparent yellow brush
                painter.setBrush(QColor(255, 255, 0, 100))
                painter.setPen(Qt.PenStyle.NoPen)
                for rect in highlight_rects:
                    # Scale coordinates by the zoom level
                    scaled_rect = QRectF(
                        rect.x0 * zoom_level,
                        rect.y0 * zoom_level,
                        (rect.x1 - rect.x0) * zoom_level,
                        (rect.y1 - rect.y0) * zoom_level
                    )
                    painter.drawRect(scaled_rect)
                painter.end()
                
            return pixmap
            
        except Exception as e:
            print(f"Error rendering page {page_index}: {e}")
            return QPixmap()

    def get_page_size(self, page_index: int) -> tuple[float, float]:
        """
        Get the original width and height of a specific page.
        Returns a tuple of (width, height), or (0.0, 0.0) if failed.
        """
        if not self.doc or page_index < 0 or page_index >= self.get_page_count():
            return 0.0, 0.0
        try:
            page = self.doc.load_page(page_index)
            rect = page.rect
            return rect.width, rect.height
        except Exception as e:
            print(f"Error getting page size for page {page_index}: {e}")
            return 0.0, 0.0

    def get_toc(self) -> list:
        """
        Retrieve the hierarchical Table of Contents (Outline) of the PDF.
        Each entry is [level, title, page_number_1_indexed].
        """
        if self.doc:
            try:
                return self.doc.get_toc()
            except Exception as e:
                print(f"Error getting TOC: {e}")
        return []

    def search_text_on_page(self, page_index: int, text: str) -> list:
        """
        Search for a text term on a specific page.
        Returns a list of fitz.Rect objects containing the matches.
        """
        if not self.doc or page_index < 0 or page_index >= self.get_page_count() or not text:
            return []
        try:
            page = self.doc.load_page(page_index)
            # fitz page.search_for searches case-insensitively by default
            return page.search_for(text)
        except Exception as e:
            print(f"Error searching text on page {page_index}: {e}")
            return []


