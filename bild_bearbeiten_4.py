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
        self.setWindowTitle("PyQt5 Comprehensive Template")
        self.setGeometry(100, 100, int(width*scale), int(height*scale))

        # Create a central widget which will hold a QTabWidget with multiple tabs
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)

        # Initialize and add tabs
        self.init_basic_widgets_tab()

    # --------------------------------------------------------------------------
    # Tabs Setup
    # --------------------------------------------------------------------------
    def init_basic_widgets_tab(self):
        """Create a tab with basic widgets (QLineEdit, QSpinBox, QComboBox, etc.)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Example of form-like layout
        form_layout = QFormLayout()
        self.name_line_edit = QLineEdit()
        form_layout.addRow("Name:", self.name_line_edit)


        layout.addLayout(form_layout)

        # Some buttons to demonstrate dialogs/messages
        button_layout = QHBoxLayout()

        scan_button = QPushButton("Scannen")
        # show_info_button.clicked.connect(self.on_show_info_clicked)
        button_layout.addWidget(scan_button)

        show_message_box_button = QPushButton("Show MessageBox")
        # show_message_box_button.clicked.connect(self.on_show_message_box_clicked)
        button_layout.addWidget(show_message_box_button)

        layout.addLayout(button_layout)

        # Add the tab to the main window
        self.central_widget.addTab(tab, "Scannen")

if __name__ == "__main__":
    app = QApplication(sys.argv)


    window = MainWindow()# Change to your video source
    window.show()
    sys.exit(app.exec_())
