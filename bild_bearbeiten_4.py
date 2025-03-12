__author__ = 'mkv-aql'
import os
# import nothing
import cv2
import pandas as pd
import ast
from Modules.class_highlight import RectangleSelector as rs #For highlighting module
from Modules.class_cutout import ImageCutoutSaver as ics #For cutout module
from Modules.class_entry_input_2 import CsvEditor as ei #For entry input module
# from Modules.class_easyOCR_V1 import OCRProcessor # for ocr detection, Moved to run_detection() function for faster app

import sys
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QComboBox, QCalendarWidget, QTabWidget, QTableWidget,
    QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QMenuBar,
    QMenu, QAction, QToolBar, QStatusBar, QMessageBox,
    QFileDialog, QColorDialog, QFontDialog, QInputDialog
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QImage, QPixmap

class MainWindow(QMainWindow):
    def __init__(self, width=800, height=600, scale=1.0):
        super().__init__()

        # Basic window setup
        self.setWindowTitle("Klingelschild-Reiniger")
        self.setGeometry(100, 100, int(width*scale), int(height*scale))
        self.setWindowIcon(QtGui.QIcon("icon/DGN_Bildmarke_orange_rgb.png"))

        # Create a central widget which will hold a QTabWidget with multiple tabs
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)

        # Initialize and add tabs
        self.init_files_tab()
        self.init_bearbeiten_tab()
        self.init_test_tab()

    # --------------------------------------------------------------------------
    # Tabs Setup
    # --------------------------------------------------------------------------
    def init_files_tab(self):
        """Create a tab with basic widgets (QLineEdit, QSpinBox, QComboBox, etc.)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Example of form-like layout
        form_layout = QFormLayout()
        name_line_edit = QLineEdit()
        form_layout.addRow("Name:", name_line_edit)

        layout.addLayout(form_layout)

        # ---------------------------------------------------------------------------
        # Tree
        example_dict = {
            "Briefkaesten_beispeil":
                [["ID Nummer 1", "Max", "[123],[456],[789],[101]"],
                 ["ID Nummer 2", "Mustermann", "[123],[456],[789],[101]"]],

            "Briefkaesten_beispeil_2":
                [["ID Nummer 2", "Mustermann", "[123],[456],[789],[101]"]]
        }
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Bildname", "Namen", "Bbox"])
        # root_item = QTreeWidgetItem(["Briefkaesten_beispeil.jpg", "", ""])
        # self.tree_widget.addTopLevelItem(root_item)
        for file_name, data in example_dict.items():
            root_item = QTreeWidgetItem([file_name, "", ""])
            self.tree_widget.addTopLevelItem(root_item)
            for row in data:
                child_item = QTreeWidgetItem(row)
                root_item.addChild(child_item)


        # for file_name, data in example_dict.items():
        #     file_item = QTreeWidgetItem([file_name, "", ""])
        #     root_item.addChild(file_item)
        #     for row in data:
        #         child_item = QTreeWidgetItem(row)
        #         file_item.addChild(child_item)

        # child1 = QTreeWidgetItem(["ID Nummer 1", "Max", "[123],[456],[789],[101]"])
        # child2 = QTreeWidgetItem(["ID Nummer 2", "Mustermann", "[123],[456],[789],[101]"])
        # root_item.addChild(child1)
        # root_item.addChild(child2)

        layout.addWidget(self.tree_widget)

        # ---------------------------------------------------------------------------
        # Create a QSpinBox to set max dimension
        self.max_size_spin_files_tab = QSpinBox()
        self.max_size_spin_files_tab.setRange(100, 8000)  # Arbitrary range: min=100, max=8000
        self.max_size_spin_files_tab.setValue(800)  # Default value
        self.max_size_spin_files_tab.setPrefix("Max Size: ")
        self.max_size_spin_files_tab.setSuffix(" px")
        self.max_size_spin_files_tab.setToolTip("Maximum width/height for the displayed image")

        # Create a QHBoxLayout for controls (button + spin box)
        controls_layout = QHBoxLayout()
        # Add the controls to the horizontal layout
        controls_layout.addWidget(self.max_size_spin_files_tab)
        # Add the controls and the image label to the main vertical layout
        layout.addLayout(controls_layout)



        # Button layout
        button_layout = QHBoxLayout()

        select_image_button = QPushButton("Bildauswahl")
        # show_message_box_button.clicked.connect(self.on_show_message_box_clicked)
        select_image_button.clicked.connect(lambda: self.open_image(from_tab='files', to_tab='edit'), )
        button_layout.addWidget(select_image_button)


        select_folder_button = QPushButton("Ordnerauswahl")
        # show_message_box_button.clicked.connect(self.on_show_message_box_clicked)
        button_layout.addWidget(select_folder_button)


        show_message_box_button = QPushButton("Hello World")
        # show_message_box_button.clicked.connect(self.on_show_message_box_clicked)
        button_layout.addWidget(show_message_box_button)

        layout.addLayout(button_layout)

        # Add the tab to the main window
        self.central_widget.addTab(tab, "Arbeitsplatz")

    def init_bearbeiten_tab(self):
        # Initialize the tab, tab layout, and buttons layout
        tab = QWidget()
        layout = QVBoxLayout(tab)

        button_layout = QHBoxLayout()

        # Create a label to display the frames of image
        self.label = QLabel("kein Bild ausgewählt")
        self.label.setAlignment(Qt.AlignCenter)

        # Set up layout for the image label
        layout.addWidget(self.label)
        self.setLayout(layout)

        scan_button = QPushButton("Scannen")
        # scan_button.clicked.connect(self.on_show_info_clicked)
        button_layout.addWidget(scan_button)

        remove_name_button = QPushButton("Namen entfernen")
        # remove_name_button.clicked.connect(self.on_show_info_clicked)
        button_layout.addWidget(remove_name_button)

        undo_remove_name_button = QPushButton("Namen entfernen rückgängig")
        # undo_remove_name_button.clicked.connect(self.on_show_info_clicked)
        button_layout.addWidget(undo_remove_name_button)

        # Add the buttons to the layout
        layout.addLayout(button_layout)

        # Add the tab to the main windows
        self.central_widget.addTab(tab, "Bild-Bearbeiten")

    def init_test_tab(self):
        # Main widget and layout
        tab = QWidget()
        main_layout = QVBoxLayout(tab)

        # Create a QHBoxLayout for controls (button + spin box)
        controls_layout = QHBoxLayout()

        # Create a QLabel to display the loaded image
        self.image_label = QLabel("No image loaded")
        self.image_label.setAlignment(Qt.AlignCenter)

        # Create a button to open the file dialog
        open_button = QPushButton("Open Image")
        # open_button.clicked.connect(self.open_image, from_tab='test')
        open_button.clicked.connect(lambda: self.open_image(from_tab='test', to_tab='test'), )

        # Create a QSpinBox to set max dimension
        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(100, 8000)  # Arbitrary range: min=100, max=8000
        self.max_size_spin.setValue(800)  # Default value
        self.max_size_spin.setPrefix("Max Size: ")
        self.max_size_spin.setSuffix(" px")
        self.max_size_spin.setToolTip("Maximum width/height for the displayed image")

        # Add the controls to the horizontal layout
        controls_layout.addWidget(open_button)
        controls_layout.addWidget(self.max_size_spin)

        # Add the controls and the image label to the main vertical layout
        main_layout.addLayout(controls_layout)
        main_layout.addWidget(self.image_label)

        # Add the tab to the main windows
        self.central_widget.addTab(tab, "Test Tab")

    # --------------------------------------------------------------------------
    # Functions Setup
    # --------------------------------------------------------------------------
    def open_image(self, from_tab='test', to_tab=''):
        """
        Open a file dialog to pick an image file, then load it using cv2,
        resize to the specified maximum dimension, and display it in the QLabel.
        """
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )

        if file_name:
            # Use OpenCV to read the image (BGR format)
            cv_img = cv2.imread(file_name)

            if cv_img is not None:
                # Convert BGR (OpenCV) to RGB
                cv_img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                # Get dimensions
                height, width, channel = cv_img_rgb.shape

                # Retrieve user-selected maximum dimension
                # (Make sure self.max_size_spin exists, i.e., if we're on the 'Test Tab')
                # Fall back if needed, or raise an AttributeError if not found.
                if hasattr(self, 'max_size_spin') and from_tab == 'test':
                    max_dim = self.max_size_spin.value()
                else:
                    max_dim = 800  # Some default if the spinbox isn't present

                if hasattr(self, 'max_size_spin_files_tab') and from_tab == 'files':
                    max_dim = self.max_size_spin_files_tab.value()
                else:
                    max_dim = 800

                # If the image exceeds max_dim in width or height, resize
                if width > max_dim or height > max_dim:
                    # Calculate the scale factor, preserving aspect ratio
                    scale = min(max_dim / width, max_dim / height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)

                    # Resize using OpenCV for efficiency
                    cv_img_rgb = cv2.resize(cv_img_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)
                    height, width, channel = cv_img_rgb.shape  # Update to new size


                # Create QImage from numpy data
                bytes_per_line = channel * width
                q_image = QImage(cv_img_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)

                # Convert QImage to QPixmap
                pixmap = QPixmap.fromImage(q_image)

                # REsize the window
                self.setGeometry(300, 100, new_width, new_height)

                # Display the image in the label
                if to_tab == 'edit':
                    self.label.setPixmap(pixmap)
                elif to_tab == 'test':
                    self.image_label.setPixmap(pixmap)
            else:
                QMessageBox.warning(self, "Error", "Failed to load image.")

if __name__ == "__main__":
    app = QApplication(sys.argv)


    window = MainWindow()# Change to your video source
    window.show()
    sys.exit(app.exec_())
