__author__ = 'mkv-aql'

# main.py

import sys
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QSpinBox, QFileDialog
)

# Import our custom clickable label
from class_clickable_image_V1 import ClickableImageLabel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Click to Get Image Coordinates")
        self.resize(800, 600)

        # Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)

        # A horizontal layout for the button & spinbox
        top_layout = QHBoxLayout()

        # Button to open an image
        self.open_button = QPushButton("Open Image")
        self.open_button.clicked.connect(self.open_image_dialog)
        top_layout.addWidget(self.open_button)

        # Spinbox for max dimension
        self.max_dim_label = QLabel("Max Pixel Size:")
        self.max_dim_spinbox = QSpinBox()
        self.max_dim_spinbox.setRange(1, 5000)
        self.max_dim_spinbox.setValue(800)  # Default
        top_layout.addWidget(self.max_dim_label)
        top_layout.addWidget(self.max_dim_spinbox)

        main_layout.addLayout(top_layout)

        # Use our custom clickable image label
        self.image_label = ClickableImageLabel()
        self.image_label.clicked_coords.connect(self.fetch_clicked_coords)
        main_layout.addWidget(self.image_label)

    def fetch_clicked_coords(self, x, y, orig_x, orig_y):
        """
        Handle the clicked coordinates.
        :param x: Clicked x-coordinate in scaled image.
        :param y: Clicked y-coordinate in scaled image.
        :param orig_x: Original x-coordinate in full-size image.
        :param orig_y: Original y-coordinate in full-size image.
        """
        print(f"Clicked coordinates (scaled): ({x}, {y})")
        print(f"Original coordinates: ({orig_x}, {orig_y})")

    def open_image_dialog(self):
        """
        Prompt the user to open an image file, display it scaled,
        and enable clicking to get coordinates.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif *.tiff)"
        )
        if not file_path:
            return

        # Load the QImage
        qimage = QImage(file_path)
        if qimage.isNull():
            self.image_label.setText("Failed to load image.")
            return

        # Get the max dimension from spinbox
        max_dim = self.max_dim_spinbox.value()

        # Set the image on the clickable label (scaled)
        self.image_label.set_image(qimage, max_dim)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
