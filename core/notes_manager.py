import os
import json
import time

class NotesManager:
    def __init__(self, pdf_path: str = None):
        """
        Initialize the Notes Manager.
        """
        self.pdf_path = pdf_path
        self.notes_path = None
        self.notes = []
        
        if pdf_path:
            self.set_pdf_path(pdf_path)

    def set_pdf_path(self, pdf_path: str) -> None:
        """
        Set active PDF path and load its associated notes.
        """
        self.pdf_path = pdf_path
        # Example: document.pdf -> document.notes.json
        if pdf_path:
            base_path = os.path.splitext(pdf_path)[0]
            self.notes_path = f"{base_path}.notes.json"
            self.load_notes()
        else:
            self.notes_path = None
            self.notes = []

    def load_notes(self) -> None:
        """
        Load notes from the JSON file if it exists.
        """
        if not self.notes_path or not os.path.exists(self.notes_path):
            self.notes = []
            return

        try:
            with open(self.notes_path, "r", encoding="utf-8") as f:
                self.notes = json.load(f)
        except Exception as e:
            print(f"Error loading notes: {e}")
            self.notes = []

    def save_notes(self) -> None:
        """
        Save notes to the JSON file.
        """
        if not self.notes_path:
            return

        try:
            # If no notes, delete the notes file to keep folder clean
            if not self.notes:
                if os.path.exists(self.notes_path):
                    os.remove(self.notes_path)
                return

            with open(self.notes_path, "w", encoding="utf-8") as f:
                json.dump(self.notes, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving notes: {e}")

    def add_note(self, page: int, text: str, note_text: str, rects: list, color: str = "yellow") -> dict:
        """
        Add a new note/highlight.
        rects: list of fitz.Rect objects.
        """
        # Convert fitz.Rect list to serializable floats list
        serialized_rects = []
        for r in rects:
            serialized_rects.append([r.x0, r.y0, r.x1, r.y1])

        note_item = {
            "id": str(int(time.time() * 1000)),
            "page": page,
            "text": text,
            "note": note_text,
            "rects": serialized_rects,
            "color": color,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        self.notes.append(note_item)
        self.save_notes()
        return note_item

    def delete_note(self, note_id: str) -> bool:
        """
        Delete a note by its ID.
        """
        original_len = len(self.notes)
        self.notes = [n for n in self.notes if n["id"] != note_id]
        
        if len(self.notes) < original_len:
            self.save_notes()
            return True
        return False

    def get_notes_for_page(self, page: int) -> list:
        """
        Retrieve all notes on a specific page.
        """
        return [n for n in self.notes if n["page"] == page]
