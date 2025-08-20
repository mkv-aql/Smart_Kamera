__author__ = 'mkv-aql'

# clickable_image_label.py

import sys
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QLabel
import cv2


class ClickableImageLabel(QLabel):
    """
    A QLabel that displays an image and captures mouse clicks.
    We store scale factors so we can map from the displayed (scaled) image
    coordinates back to the original image coordinates.
    """

    # Define a signal that emits two integers
    clicked_coords = pyqtSignal(int, int, int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScaledContents(False)  # We'll do our own scaling
        self._original_image = None  # Store full-size QImage
        self._scaled_pixmap = None  # QPixmap for display
        self._scale_ratio_x = 1.0
        self._scale_ratio_y = 1.0
        self.setAlignment(Qt.AlignCenter)

        # Store references
        self._cv_img = None  # Original image as NumPy array (BGR)

    def set_image(self, qimage, max_dim):
        """
        Set the original image and scale it to fit within max_dim (width or height).
        """
        self._original_image = qimage
        if qimage.isNull():
            self._scaled_pixmap = None
            self.setText("Failed to load image.")
            return

        # Original dimensions
        orig_w = qimage.width()
        orig_h = qimage.height()

        # Compute scaled dimensions based on max_dim
        ratio = min(max_dim / orig_w, max_dim / orig_h) if max_dim > 0 else 1.0
        new_w = int(orig_w * ratio)
        new_h = int(orig_h * ratio)

        # Convert QImage -> QPixmap
        pixmap = QPixmap.fromImage(qimage)

        # Scale the QPixmap to new size (keeping aspect ratio)
        scaled_pix = pixmap.scaled(
            new_w, new_h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )

        self._scaled_pixmap = scaled_pix
        self.setPixmap(scaled_pix)

        # Store scale ratios for coordinate mapping
        self._scale_ratio_x = orig_w / new_w
        self._scale_ratio_y = orig_h / new_h

    def set_cv_image(self, cv_img, max_dim):
        """
        Set the original OpenCV image (NumPy array, BGR format),
        then convert to QImage, scale it to max_dim, and display it.
        """
        if cv_img is None or cv_img.size == 0:
            self._cv_img = None
            self._scaled_pixmap = None
            self.setText("Failed to load image.")
            return

        self._cv_img = cv_img

        # Original dimensions
        orig_h, orig_w, orig_c = cv_img.shape  # BGR -> shape = (height, width, channels)

        # Convert from BGR to RGB
        cv_img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)

        # Wrap the NumPy data in a QImage
        qimage = QImage(
            cv_img_rgb.data,
            orig_w,
            orig_h,
            3 * orig_w,  # bytes per line (3 channels * width)
            QImage.Format_RGB888
        )

        # Compute scale ratio so neither width nor height exceeds max_dim
        ratio = min(max_dim / orig_w, max_dim / orig_h) if max_dim > 0 else 1.0
        if ratio > 1.0:
            ratio = 1.0  # No need to upscale if original is smaller than max_dim

        new_w = int(orig_w * ratio)
        new_h = int(orig_h * ratio)

        # Convert QImage -> QPixmap
        pixmap = QPixmap.fromImage(qimage)

        # Scale the pixmap
        scaled_pix = pixmap.scaled(
            new_w, new_h,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self._scaled_pixmap = scaled_pix
        self.setPixmap(scaled_pix)

        # Store the ratio for coordinate mapping
        self._scale_ratio_x = orig_w / new_w
        self._scale_ratio_y = orig_h / new_h

    def mousePressEvent(self, event):
        """
        Override to capture the mouse click coordinates, map them back to the
        original image's coordinate space, and print them.
        """
        if self._scaled_pixmap is None or self._original_image is None or self._cv_img is None:
            return

        # Get position in the label
        click_x = event.pos().x()
        click_y = event.pos().y()


        # The image might be centered if the label is bigger than the pixmap
        pixmap_w = self._scaled_pixmap.width()
        pixmap_h = self._scaled_pixmap.height()

        label_w = self.width()
        label_h = self.height()

        # Top-left corner of the pixmap within the label
        offset_x = (label_w - pixmap_w) // 2
        offset_y = (label_h - pixmap_h) // 2

        # Check if the click is actually on the displayed image
        if not (offset_x <= click_x < offset_x + pixmap_w and offset_y <= click_y < offset_y + pixmap_h):
            return  # Clicked outside the image area


        # Compute coordinates within the scaled image
        scaled_x = click_x - offset_x
        scaled_y = click_y - offset_y

        # Map back to original image coordinates
        orig_x = int(scaled_x * self._scale_ratio_x)
        orig_y = int(scaled_y * self._scale_ratio_y)

        self.clicked_coords.emit(scaled_x, scaled_y, orig_x, orig_y)  # Emit the clicked coordinates

        # print(f"Clicked at scaled=({scaled_x}, {scaled_y}), original=({orig_x}, {orig_y})")

        # return scaled_x, scaled_y, orig_x, orig_y  # This return will not work in PyQt5, it is an event handler
        # Instead, you can emit a signal or call a method to handle the coordinates

        # self.push_coor(scaled_x, scaled_y, orig_x, orig_y)  # Call the function to handle coordinates



    def push_coor(self, scaled_x, scaled_y, orig_x, orig_y):
        """
        Function to handle the coordinates.
        This function can be modified to do whatever is needed with the coordinates.
        """
        print(f"Coordinates: Scaled=({scaled_x}, {scaled_y}), Original=({orig_x}, {orig_y})")






