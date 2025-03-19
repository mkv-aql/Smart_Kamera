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
from Modules.class_magnification_feature import ImageLabel #For magnification module

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
from PyQt5.QtCore import QTimer, Qt, QPoint, QThread, QObject, pyqtSignal, QMutex
from PyQt5.QtGui import QImage, QPixmap


class MainWindow(QMainWindow):
    def __init__(self, width=800, height=600, scale=1.0):
        super().__init__()

        # Basic window setup
        self.setWindowTitle("Klingelschild-Reiniger")
        self.setGeometry(100, 100, int(width*scale), int(height*scale))
        self.setWindowIcon(QtGui.QIcon("icon/DGN_Bildmarke_orange_rgb.png"))

        # Shared image for threads, to safely pass data between threads
        self.shared_image = QImage()
        self.mutex = QMutex() # Mutex for shared list
        self.thread = None # Thread object
        self.worker = None # Worker object

        # Create a central widget which will hold a QTabWidget with multiple tabs
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)

        # ------------- State / Data -------------
        self.cv_img_original = None  # Original full-res image (numpy, RGB)
        self.cv_img_display = None  # Scaled-down image for display
        self.is_magnifying = False
        self.magnify_scale_factor = 4  # How much to zoom in
        self.magnify_window_size = 50  # Half-size of sampling window in original coordinates

        # Create tabs
        self.files_tab = QWidget()
        self.edit_tab = QWidget()
        self.test_tab = QWidget()


        # Add the tab to the main window
        self.central_widget.addTab(self.files_tab, "Arbeitsplatz")
        self.central_widget.addTab(self.edit_tab, "Bild-Bearbeiten")

        # Initialize and add tabs
        self.init_files_tab()
        self.init_edit_tab()
        self.init_test_tab()

    # --------------------------------------------------------------------------
    # Tabs Setup
    # --------------------------------------------------------------------------
    def init_files_tab(self):
        """Create a tab with basic widgets (QLineEdit, QSpinBox, QComboBox, etc.)."""
        # files_tab = QWidget() # Moved to class level
        layout = QVBoxLayout()
        self.files_tab.setLayout(layout)

        # Example of form-like layout
        name_line_edit = QLineEdit()
        form_layout = QFormLayout()
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
        tree_widget = QTreeWidget()
        tree_widget.setHeaderLabels(["Bildname", "Namen", "Bbox"])
        # root_item = QTreeWidgetItem(["Briefkaesten_beispeil.jpg", "", ""])
        # self.tree_widget.addTopLevelItem(root_item)
        for file_name, data in example_dict.items():
            root_item = QTreeWidgetItem([file_name, "", ""])
            tree_widget.addTopLevelItem(root_item)
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

        layout.addWidget(tree_widget)

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



    def init_edit_tab(self):
        # Initialize the tab, tab layout, and buttons layout
        layout = QVBoxLayout() # Main Layout
        self.edit_tab.setLayout(layout) # set layout to the tab

        # Horizonal layout for the image display area + magnified preview side-by-side
        hor_layout = QHBoxLayout() # secondary layout
        layout.addLayout(hor_layout) # add secondary layout to the main layout


        self.label_edit_tab = ImageLabel(parent=self)
        self.label_edit_tab.setText("kein Bild ausgewählt")
        hor_layout.addWidget(self.label_edit_tab, stretch=3)


        button_layout = QHBoxLayout() # Control layout

        self.scan_button = QPushButton("Scannen")
        self.scan_button.clicked.connect(self.scan_image)
        button_layout.addWidget(self.scan_button)

        remove_name_button = QPushButton("Namen entfernen")
        # remove_name_button.clicked.connect(self.on_show_info_clicked)
        button_layout.addWidget(remove_name_button)

        undo_remove_name_button = QPushButton("Namen entfernen rückgängig")
        # undo_remove_name_button.clicked.connect(self.on_show_info_clicked)
        button_layout.addWidget(undo_remove_name_button)

        # Add the buttons to the layout
        layout.addLayout(button_layout)




        # Label that shows the magnified patch
        self.magnify_label = QLabel("Magnified View")
        self.magnify_label.setFixedSize(450, 450)  # A fixed size for the magnifying preview
        self.magnify_label.setAlignment(Qt.AlignCenter)
        self.magnify_label.setStyleSheet("border: 1px solid black; background-color: #CCC;")
        self.magnify_label.setVisible(False)  # Hidden by default (until magnify is ON)
        hor_layout.addWidget(self.magnify_label, stretch=1)

        # -- Button: Toggle Magnify --
        self.magnify_button = QPushButton("Magnify Mode: OFF")
        self.magnify_button.setCheckable(True)
        self.magnify_button.clicked.connect(self.toggle_magnify)
        button_layout.addWidget(self.magnify_button)  # Control layout



    def init_test_tab(self):
        # Main widget and layout
        tab = QWidget()
        main_layout = QVBoxLayout(tab)

        # Create a QHBoxLayout for controls (button + spin box)
        controls_layout = QHBoxLayout()

        # Create a QLabel to display the loaded image
        self.image_label_test_tab = QLabel("No image loaded")
        self.image_label_test_tab.setAlignment(Qt.AlignCenter)

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
        main_layout.addWidget(self.image_label_test_tab)

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
        self.img_name, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp *.tiff);;All Files (*)"
        )

        # print(f'img_name: {self.img_name}') # Debugging

        if self.img_name:
            # Use OpenCV to read the image (BGR format)
            cv_img = cv2.imread(self.img_name)

            if cv_img is not None:
                # Convert BGR (OpenCV) to RGB
                self.cv_img_rgb_original = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
                # Get dimensions
                orig_height, orig_width, channel = self.cv_img_rgb_original.shape

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
                if orig_width > max_dim or orig_height > max_dim:
                    # Calculate the scale factor, preserving aspect ratio
                    scale = min(max_dim / orig_width, max_dim / orig_height)
                    disp_width = int(orig_width * scale)
                    disp_height = int(orig_height * scale)

                    # Resize using OpenCV for efficiency
                    cv_img_rgb_display = cv2.resize(self.cv_img_rgb_original,
                                            (disp_width, disp_height),
                                            interpolation=cv2.INTER_AREA)
                else:
                    disp_width = orig_width  # No need to resize
                    disp_height = orig_height
                    # No need to resize
                    height, width, channel = self.cv_img_rgb_display.copy()  # create copy

                """
                ## MOVED to show_image_in_label function
                # Create QImage from numpy data
                bytes_per_line = channel * width
                q_image = QImage(cv_img_rgb_display.data, width, height, bytes_per_line, QImage.Format_RGB888) # moved to show_image_in_label function

                # Convert QImage to QPixmap
                pixmap = QPixmap.fromImage(q_image) # moved to show_image_in_label function

                """

                #Store the scaled / unchanged result in the instance variable:
                self.cv_img_rgb_display = cv_img_rgb_display

                # REsize the window
                self.setGeometry(300, 100, disp_width, disp_height)

                # Display the image in the label
                if to_tab == 'edit':
                    # self.label.setPixmap(pixmap)
                    self.show_image_in_label(cv_img_rgb_display, self.label_edit_tab)
                elif to_tab == 'test':
                    # self.image_label_test_tab.setPixmap(pixmap)
                    self.show_image_in_label(cv_img_rgb_display, self.image_label_test_tab)

                # Switch to the 'Edit Tab' automatically
                if to_tab == 'edit':
                    self.central_widget.setCurrentIndex(1)
                elif to_tab == 'test':
                    self.central_widget.setCurrentIndex(2)

            else:
                QMessageBox.warning(self, "Error", "Failed to load image.")

    def show_image_in_label(self, img_rgb, label):
        """Convert a numpy RGB image to QPixmap and display it in the given label."""
        if img_rgb is None:
            return

        height, width, channel = img_rgb.shape
        bytes_per_line = channel * width
        q_image = QImage(img_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_image)
        label.setPixmap(pixmap)

    def toggle_magnify(self, checked):
        """
        Turn magnify mode on/off. If on, show the magnify_label and update text.
        """
        self.is_magnifying = checked
        if checked:
            self.magnify_button.setText("Magnify Mode: ON")
            self.magnify_label.setVisible(True)
            self.magnify_label.setText("Hover over the image")
        else:
            self.magnify_button.setText("Magnify Mode: OFF")
            self.magnify_label.setVisible(False)

    def magnify_at(self, pos: QPoint):
        """
        Show a zoomed-in region from the ORIGINAL full-res image,
        based on the mouse position in the DISPLAYED (scaled) image.
        """
        if self.cv_img_rgb_original is None or self.cv_img_rgb_display is None:
            return  # No image loaded

        # Get the label’s current size vs. the actual displayed image’s shape
        # label_width = self.image_label.width()
        # label_height = self.image_label.height()
        label_width = self.label_edit_tab.width()
        label_height = self.label_edit_tab.height()

        disp_h, disp_w, _ = self.cv_img_rgb_display.shape
        orig_h, orig_w, _ = self.cv_img_rgb_original.shape

        # Safety check
        if label_width == 0 or label_height == 0:
            return

        # Convert label coords -> displayed image coords (which might differ if the label is resized by layout).
        # Usually, the pixmap is drawn at its "natural" size, but we do a ratio approach to be robust.
        displayed_x = int(pos.x() / label_width * disp_w)
        displayed_y = int(pos.y() / label_height * disp_h)

        # Clamp to display boundaries
        displayed_x = max(0, min(displayed_x, disp_w - 1))
        displayed_y = max(0, min(displayed_y, disp_h - 1))

        # Now map from displayed coords to original coords.
        # We know the scale factor used: scale_x = disp_w / orig_w, scale_y = disp_h / orig_h
        # So original_x = displayed_x * (orig_w / disp_w).
        # Similarly for y.
        scale_x = orig_w / disp_w
        scale_y = orig_h / disp_h

        orig_x = int(displayed_x * scale_x)
        orig_y = int(displayed_y * scale_y)

        # Clamp to original boundaries
        orig_x = max(0, min(orig_x, orig_w - 1))
        orig_y = max(0, min(orig_y, orig_h - 1))

        # Extract a patch around (orig_x, orig_y) from the full-res image
        half_w = self.magnify_window_size
        x1 = max(0, orig_x - half_w)
        y1 = max(0, orig_y - half_w)
        x2 = min(orig_w, orig_x + half_w)
        y2 = min(orig_h, orig_y + half_w)

        patch = self.cv_img_rgb_original[y1:y2, x1:x2]
        if patch.size == 0:
            return

        # Zoom the patch up by self.magnify_scale_factor
        patch_h, patch_w, _ = patch.shape
        zoomed_w = patch_w * self.magnify_scale_factor
        zoomed_h = patch_h * self.magnify_scale_factor

        zoomed_patch = cv2.resize(patch, (zoomed_w, zoomed_h), interpolation=cv2.INTER_LINEAR)
        self.show_image_in_label(zoomed_patch, self.magnify_label)

    def scan_image(self):
        print("Scan image clicked")

        # Disable button to avoid multiple clicks
        self.scan_button.setEnabled(False)
        self.image_label.setText("Loading image... please wait.")
        self.thread = QThread() # Create a QThread object
        self.worker = Worker(shared_image=self.shared_image, mutex=self.mutex, file_path=self.img_name) # Create a worker object

        self.worker.moveToThread(self.thread)

        # Connect signals:
        # - Start the worker's run method when the thread starts
        self.thread.started.connect(self.worker.run)

        # - When the worker finishes, clean up the thread/worker
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        # - Re-enable the button after the thread finishes
        self.thread.finished.connect(lambda: self.load_button.setEnabled(True))

        # Start the thread
        self.thread.start()

    def scan_image_stop_thread(self):
        """
        Stop thread and worker
        """
        if self.worker:
            self.worker.stop()
            self.worker = None


class Worker(QObject):
    """
    Worker thread for running the OCR detection.

    """

    finished = pyqtSignal() # Signal to indicate that the worker has finished
    progress = pyqtSignal(str) # Signal to report progress

    def __init__(self, shared_image: QImage, mutex: QMutex, file_path: str):
        super().__init__()

        self.shared_image = shared_image
        self.mutex = mutex
        self.file_path = file_path

    def run(self):
        """
        Long-running task that will be started in a separate thread.
        """
        self.progress.emit("[Worker] Starting to load image ...")
        from Modules.class_easyOCR_V1 import \
            OCRProcessor  # for ocr detection, Moved to run_detection() function for faster app

        self.img_name = QImage(self.file_path)

        if self.img_name is not None:
            # Emit progress signal
            self.progress.emit("Worker: Successfully loaded image in worker. Now locking mutex...")
            # Lock the mutex before writing to the shared image
            self.mutex.lock()

            # Initialize the OCR processor
            ocr_processor = OCRProcessor()

            # Perform OCR on the given image
            image_path = self.img_name
            df_ocr_results = ocr_processor.ocr(image_path)
            # print(df_ocr_results.head(5)) # Debugging

            save_path = '../csv_speichern'
            # Save the OCR results to a CSV file
            ocr_processor.save_to_csv(df_ocr_results, image_path, save_path)
            print(df_ocr_results)

            self.mutex.unlock() # Unlock the mutex after writing to the shared image
            self.progress.emit("[Worker] Image done")
            self.finished.emit()
        else:
            print("No image selected")
            self.progress.emit("[Worker] Image process failed")
            self.finished.emit()


if __name__ == "__main__":
    app = QApplication(sys.argv)


    window = MainWindow()# Change to your video source
    window.show()
    sys.exit(app.exec_())
