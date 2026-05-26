from core.pdf_engine import PDFEngine

class TextExtractor:
    def __init__(self, pdf_engine: PDFEngine):
        """
        Initialize the Text Extractor with a PDF engine.
        """
        self.pdf_engine = pdf_engine

    def extract_page_text(self, page_index: int) -> str:
        """
        Extract text from a specific page.
        """
        if not self.pdf_engine.doc or page_index < 0 or page_index >= self.pdf_engine.get_page_count():
            return ""
        try:
            page = self.pdf_engine.doc.load_page(page_index)
            return page.get_text()
        except Exception as e:
            print(f"Error extracting text from page {page_index}: {e}")
            return ""

    def extract_all_text(self) -> str:
        """
        Extract text from all pages of the document.
        """
        if not self.pdf_engine.doc:
            return ""
        
        text_list = []
        for i in range(self.pdf_engine.get_page_count()):
            page_text = self.extract_page_text(i)
            text_list.append(f"--- Page {i + 1} ---\n{page_text}\n")
            
        return "\n".join(text_list)

    def extract_to_file(self, output_path: str) -> bool:
        """
        Extract all text and save it to a file.
        Returns True if successful, False otherwise.
        """
        if not self.pdf_engine.doc:
            return False
            
        try:
            text = self.extract_all_text()
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            return True
        except Exception as e:
            print(f"Error saving extracted text to file {output_path}: {e}")
            return False
