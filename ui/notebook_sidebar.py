from PyQt6.QtWidgets import QDockWidget, QListWidget, QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
from PyQt6.QtCore import Qt, pyqtSignal
from core.state import DocumentState
from core.notes_manager import NotesManager

class PDFNotebookSidebar(QDockWidget):
    # Signals
    note_selected = pyqtSignal(dict)  # Emitted when a note is clicked
    note_deleted = pyqtSignal()       # Emitted after a note is deleted

    def __init__(self, state: DocumentState, notes_manager: NotesManager, parent=None):
        """
        Initialize the PDF Notebook Sidebar.
        """
        super().__init__("Notebook & Ghi chú", parent)
        self.state = state
        self.notes_manager = notes_manager
        
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)
        
        self.init_ui()
        self.connect_signals()

    def init_ui(self) -> None:
        """
        Setup the QListWidget.
        """
        self.list_widget = QListWidget()
        # Clean styling
        self.list_widget.setStyleSheet("QListWidget { border: none; padding: 5px; }")
        
        # When an item is clicked, handle navigation
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        
        self.setWidget(self.list_widget)

    def connect_signals(self) -> None:
        """
        Connect sync signals.
        """
        # Sync with document load / close
        self.state.document_loaded.connect(self.load_notes_list)
        self.state.document_closed.connect(self.clear_notes_list)

    def load_notes_list(self) -> None:
        """
        Fetch notes from NotesManager and populate QListWidget.
        """
        self.list_widget.clear()
        
        if not self.notes_manager.notes:
            item = QListWidgetItem(self.list_widget)
            item.setText("No notes or highlights yet.")
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            return

        # Sort notes by page index first
        sorted_notes = sorted(self.notes_manager.notes, key=lambda x: (x["page"], x["created_at"]))

        for note in sorted_notes:
            # Create list item
            item = QListWidgetItem(self.list_widget)
            
            # Create custom widget representation for the list item
            item_widget = QWidget()
            layout = QHBoxLayout(item_widget)
            layout.setContentsMargins(5, 5, 5, 5)
            layout.setSpacing(8)
            
            # Left side content (text)
            text_container = QWidget()
            text_layout = QVBoxLayout(text_container)
            text_layout.setContentsMargins(0, 0, 0, 0)
            text_layout.setSpacing(2)
            
            # 1. Header (Page + color bullet)
            color_emoji = "🟡"
            if note.get("color") == "green":
                color_emoji = "🟢"
            elif note.get("color") == "pink":
                color_emoji = "💗"
            elif note.get("color") == "none":
                color_emoji = "📝"
                
            header_label = QLabel(f"{color_emoji} Page {note['page'] + 1}")
            header_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #8e8e93;")
            text_layout.addWidget(header_label)
            
            # 2. Quotation (original PDF text)
            quote = note.get("text", "")
            if len(quote) > 45:
                quote = f"{quote[:45]}..."
            quote_label = QLabel(f"\"{quote}\"")
            quote_label.setWordWrap(True)
            quote_label.setStyleSheet("font-style: italic; color: #757575; font-size: 12px;")
            text_layout.addWidget(quote_label)
            
            # 3. User Note content (if any)
            note_text = note.get("note", "")
            if note_text:
                note_label = QLabel(note_text)
                note_label.setWordWrap(True)
                note_label.setStyleSheet("font-weight: 500; font-size: 12px;")
                text_layout.addWidget(note_label)
                
            layout.addWidget(text_container, stretch=1)
            
            # Right side button (Delete)
            btn_delete = QPushButton("✖")
            btn_delete.setFlat(True)
            btn_delete.setToolTip("Delete note")
            btn_delete.setStyleSheet("""
                QPushButton {
                    color: #ff3333;
                    font-weight: bold;
                    max-width: 25px;
                    border: none;
                    background: transparent;
                }
                QPushButton:hover {
                    background-color: rgba(255, 51, 51, 0.1);
                    border-radius: 4px;
                }
            """)
            # Bind deletion with specific note ID
            btn_delete.clicked.connect(lambda checked, n_id=note["id"]: self.delete_note(n_id))
            layout.addWidget(btn_delete, alignment=Qt.AlignmentFlag.AlignVCenter)
            
            # Save note dictionary reference in the ListWidgetItem data role
            item.setData(Qt.ItemDataRole.UserRole, note)
            
            # Set sizes and set widget
            item.setSizeHint(item_widget.sizeHint())
            self.list_widget.setItemWidget(item, item_widget)

    def clear_notes_list(self) -> None:
        """
        Clear list items.
        """
        self.list_widget.clear()

    def delete_note(self, note_id: str) -> None:
        """
        Trigger deletion of note.
        """
        reply = QMessageBox.question(
            self,
            "Confirm Delete",
            "Are you sure you want to delete this highlight/note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            success = self.notes_manager.delete_note(note_id)
            if success:
                self.load_notes_list()
                self.note_deleted.emit()

    def on_item_clicked(self, item: QListWidgetItem) -> None:
        """
        Triggered when note list item is clicked. Emits signal to parent window.
        """
        note = item.data(Qt.ItemDataRole.UserRole)
        if note and isinstance(note, dict):
            self.note_selected.emit(note)
