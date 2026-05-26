from PyQt6.QtCore import QObject, pyqtSignal

class DocumentState(QObject):
    # Signals for state changes
    page_changed = pyqtSignal(int)
    zoom_changed = pyqtSignal(float)
    fit_mode_changed = pyqtSignal(str)  # 'width', 'height', or 'none'
    theme_changed = pyqtSignal(str)    # 'light' or 'dark'
    document_loaded = pyqtSignal()
    document_closed = pyqtSignal()

    def __init__(self):
        """
        Initialize the central Document State.
        """
        super().__init__()
        self._current_page = 0
        self._total_pages = 0
        self._zoom_level = 1.0
        self._fit_mode = 'none'  # 'width', 'height', 'none'
        self._theme = 'light'    # 'light', 'dark'
        self._is_loaded = False

    # Getters and Setters with validation and signals
    @property
    def current_page(self) -> int:
        return self._current_page

    @current_page.setter
    def current_page(self, page: int) -> None:
        if not self._is_loaded:
            return
        # Clamp page index between 0 and total_pages - 1
        page = max(0, min(page, self._total_pages - 1))
        if self._current_page != page:
            self._current_page = page
            self.page_changed.emit(page)

    @property
    def total_pages(self) -> int:
        return self._total_pages

    @property
    def zoom_level(self) -> float:
        return self._zoom_level

    @zoom_level.setter
    def zoom_level(self, zoom: float) -> None:
        # Clamp zoom level between 30% and 300%
        zoom = max(0.3, min(zoom, 3.0))
        if self._zoom_level != zoom:
            self._zoom_level = zoom
            self.zoom_changed.emit(zoom)

    @property
    def fit_mode(self) -> str:
        return self._fit_mode

    @fit_mode.setter
    def fit_mode(self, mode: str) -> None:
        if mode in ('width', 'height', 'none'):
            if self._fit_mode != mode:
                self._fit_mode = mode
                self.fit_mode_changed.emit(mode)

    @property
    def theme(self) -> str:
        return self._theme

    @theme.setter
    def theme(self, theme_name: str) -> None:
        if theme_name in ('light', 'dark'):
            if self._theme != theme_name:
                self._theme = theme_name
                self.theme_changed.emit(theme_name)

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    # State modification helpers
    def load_document(self, total_pages: int) -> None:
        """
        Call when a document is successfully loaded.
        """
        self._total_pages = total_pages
        self._current_page = 0
        self._zoom_level = 1.0
        self._fit_mode = 'none'
        self._is_loaded = True
        self.document_loaded.emit()

    def close_document(self) -> None:
        """
        Call when the document is closed.
        """
        self._total_pages = 0
        self._current_page = 0
        self._zoom_level = 1.0
        self._fit_mode = 'none'
        self._is_loaded = False
        self.document_closed.emit()

    def next_page(self) -> None:
        """
        Go to the next page if possible.
        """
        if self._is_loaded and self._current_page < self._total_pages - 1:
            self.current_page = self._current_page + 1

    def prev_page(self) -> None:
        """
        Go to the previous page if possible.
        """
        if self._is_loaded and self._current_page > 0:
            self.current_page = self._current_page - 1

    def zoom_in(self, step: float = 0.1) -> None:
        """
        Increase zoom level by a step.
        """
        # If zooming, fit mode should be disabled
        self.fit_mode = 'none'
        self.zoom_level = self._zoom_level + step

    def zoom_out(self, step: float = 0.1) -> None:
        """
        Decrease zoom level by a step.
        """
        # If zooming, fit mode should be disabled
        self.fit_mode = 'none'
        self.zoom_level = self._zoom_level - step

    def toggle_theme(self) -> None:
        """
        Toggle between light and dark themes.
        """
        self.theme = 'dark' if self._theme == 'light' else 'light'
