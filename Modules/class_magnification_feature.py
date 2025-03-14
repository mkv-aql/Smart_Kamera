__author__ = 'mkv-aql'
from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, QPoint

class ImageLabel(QLabel):
    """
    Custom QLabel to display the image and handle mouse move events
    for the magnification feature.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent  # Reference to MainWindow
        self.setMouseTracking(True)  # Enable mouse tracking (move events even without pressing a button)
        self.setAlignment(Qt.AlignCenter)

    def mouseMoveEvent(self, event):
        """If magnify mode is on, call the parent's magnify method at the current mouse position."""
        if self.parent_window is not None and self.parent_window.is_magnifying:
            self.parent_window.magnify_at(event.pos())
        super().mouseMoveEvent(event)