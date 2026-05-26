from PyQt6.QtWidgets import QDockWidget, QTreeWidget, QTreeWidgetItem
from PyQt6.QtCore import Qt
from core.state import DocumentState
from core.pdf_engine import PDFEngine

class PDFSidebar(QDockWidget):
    def __init__(self, state: DocumentState, pdf_engine: PDFEngine, parent=None):
        """
        Initialize the PDF Sidebar.
        """
        super().__init__("Document Outline", parent)
        self.state = state
        self.pdf_engine = pdf_engine
        
        # Configure Dock Widget settings
        self.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea | Qt.DockWidgetArea.RightDockWidgetArea)
        self.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetMovable | QDockWidget.DockWidgetFeature.DockWidgetClosable)
        
        self.init_ui()
        self.connect_signals()

    def init_ui(self) -> None:
        """
        Setup the QTreeWidget.
        """
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        # Make the tree look modern and clean
        self.tree.setStyleSheet("QTreeWidget { border: none; padding: 5px; }")
        self.setWidget(self.tree)

    def connect_signals(self) -> None:
        """
        Connect signals and slots.
        """
        # Change page when an item in TOC is clicked
        self.tree.itemClicked.connect(self.on_item_clicked)
        
        # Sync with document load / close
        self.state.document_loaded.connect(self.load_outline)
        self.state.document_closed.connect(self.clear_outline)

    def load_outline(self) -> None:
        """
        Fetch Table of Contents from engine and populate QTreeWidget.
        """
        self.tree.clear()
        toc = self.pdf_engine.get_toc()
        
        if not toc:
            # Fallback when there is no outline
            item = QTreeWidgetItem(self.tree)
            item.setText(0, "No outline available")
            # Disable selection/interaction for the placeholder
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            return

        # Stack to track the current parent item for each level
        # Level 0 is the root TreeWidget itself
        stack = {0: self.tree}
        
        for level, title, page in toc:
            # Determine the parent widget based on level
            parent = stack.get(level - 1)
            if parent is None:
                # If level jumps erratically, attach to the root tree
                parent = self.tree
                
            item = QTreeWidgetItem(parent)
            item.setText(0, title)
            # PyMuPDF pages in TOC are 1-indexed, we store them 0-indexed
            item.setData(0, Qt.ItemDataRole.UserRole, page - 1)
            
            # Save the current item as the parent for subsequent sub-items
            stack[level] = item
            
        # Expand all outline folders by default
        self.tree.expandAll()

    def clear_outline(self) -> None:
        """
        Clear all outline items.
        """
        self.tree.clear()

    def on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handle item click. Jump to the page stored in the item.
        """
        page_index = item.data(0, Qt.ItemDataRole.UserRole)
        if page_index is not None and page_index >= 0:
            self.state.current_page = page_index
