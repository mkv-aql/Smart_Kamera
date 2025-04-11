__author__ = 'mkv-aql'

# import nothing
import cv2, csv, ast, time, threading, os, sys
import pandas as pd
from pygments import highlight
#comment

from Modules.class_clickable_image_V1 import ClickableImageLabel # For clickable image label
from Modules.class_highlight import RectangleSelector as rs #For highlighting module
from Modules.class_cutout import ImageCutoutSaver as ics #For cutout module
from Modules.class_entry_input_2 import CsvEditor as ei #For entry input module
# from Modules.class_easyOCR_V1 import OCRProcessor # for ocr detection, Moved to run_detection() function for faster app
from Modules.class_magnification_feature import ImageLabel #For magnification module

from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog,
    QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QSpinBox, QDoubleSpinBox,
    QComboBox, QCalendarWidget, QTabWidget, QTableWidget,
    QTableWidgetItem, QTreeWidget, QTreeWidgetItem, QMenuBar,
    QMenu, QAction, QToolBar, QStatusBar, QMessageBox,
    QFileDialog, QColorDialog, QFontDialog, QInputDialog, QAbstractItemView, QProgressDialog
)
from PyQt5.QtCore import QTimer, Qt, QPoint, QThread, QObject, pyqtSignal, QMutex, QDir, QEvent
from PyQt5.QtGui import QImage, QPixmap


class MainWindow(QMainWindow):
    def __init__(self, width=800, height=600, scale=1.0):
        super().__init__()

        # Basic window setup
        self.setWindowTitle("Klingelschild-Reiniger")
        self.setGeometry(1000, 100, int(width*scale), int(height*scale)) # Set window location
        self.setWindowIcon(QtGui.QIcon("icon/DGN_Bildmarke_orange_rgb.png"))


        # Create a central widget which will hold a QTabWidget with multiple tabs
        self.central_widget = QTabWidget()
        self.setCentralWidget(self.central_widget)

        # ------------- State / Data -------------
        self.cv_img_original = None  # Original full-res image (numpy, RGB)
        self.cv_img_display = None  # Scaled-down image for display
        self.is_magnifying = False
        self.magnify_scale_factor = 4  # How much to zoom in
        self.magnify_window_size = 50  # Half-size of sampling window in original coordinates
        self.scanner_active_status = False # Scanner status
        self.jump_to_image = False # Jump to image status, True will jump to image tab after selected
        self.remove_name_mode_status = False # Remove name mode status

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

        # Declare threads
        self.run_scanner_thread = threading.Thread(target=self.scanner_activated_thread)

        # clickable image label
        # We'll store the original image dimensions and the ratio
        self.original_width = 0
        self.original_height = 0
        self.scale_ratio_x = 1.0
        self.scale_ratio_y = 1.0

        # directory
        self.csv_path = 'csv_speichern'
        self.csv_edit = 'csv_bearbeiten'



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


        # ------------- CSV Tree widget -------------
        self.csv_tree_widget = QTreeWidget()
        self.csv_tree_widget.setHeaderLabels(["Bildname", "Namen", "Bbox"])
        # Make items editable by double-click:
        self.csv_tree_widget.setEditTriggers(QAbstractItemView.DoubleClicked)
        layout.addWidget(self.csv_tree_widget)
        # Populate from example_dict on startup
        self.populate_tree_from_dict()

        # ------------- Image Tree widget -------------
        self.image_tree_widget = QTreeWidget()
        self.image_tree_widget.setHeaderLabels(["Bildname", "CSV-Datei"])
        self.image_tree_widget.itemDoubleClicked.connect(self.image_tree_item_double_clicked)
        layout.addWidget(self.image_tree_widget)

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
        select_image_button.clicked.connect(lambda: self.open_image_dialog(from_tab='files', to_tab='edit'), )
        button_layout.addWidget(select_image_button)


        select_folder_button = QPushButton("Ordnerauswahl")
        select_folder_button.clicked.connect(self.open_image_folder)
        button_layout.addWidget(select_folder_button)


        csv_open_button = QPushButton("CSV-Datei öffnen")
        csv_open_button.clicked.connect(self.open_csv_dialog)
        button_layout.addWidget(csv_open_button)


        csv_save_button = QPushButton("CSV-Datei speichern")
        csv_save_button.clicked.connect(self.save_csv_dialog)
        button_layout.addWidget(csv_save_button)


        scan_all_image_button = QPushButton("Alle Bilder scannen ")
        scan_all_image_button.clicked.connect(self.scan_all_image)
        button_layout.addWidget(scan_all_image_button)

        layout.addLayout(button_layout)



    def init_edit_tab(self):
        # Initialize the tab, tab layout, and buttons layout
        layout = QVBoxLayout() # Main Layout
        self.edit_tab.setLayout(layout) # set layout to the tab

        # Horizonal layout for the image display area + magnified preview side-by-side
        self.hor_layout = QHBoxLayout() # secondary layout
        layout.addLayout(self.hor_layout) # add secondary layout to the main layout


        self.label_edit_tab = ImageLabel(parent=self)
        self.label_edit_tab.setText("kein Bild ausgewählt")
        self.hor_layout.addWidget(self.label_edit_tab, stretch=3)

        # Install the event filter so we can catch mouse presses
        self.label_edit_tab.installEventFilter(self)


        button_layout = QHBoxLayout() # Control layout

        self.activate_scanner_button = QPushButton("Scanner aktivieren")
        self.activate_scanner_button.clicked.connect(self.activate_scanner)
        button_layout.addWidget(self.activate_scanner_button)

        self.scan_button = QPushButton("Scannen")
        self.scan_button.clicked.connect(self.scan_image)
        button_layout.addWidget(self.scan_button)

        self.remove_name_button = QPushButton("Namen entfernen")
        self.remove_name_button.clicked.connect(self.remove_name_mode)
        button_layout.addWidget(self.remove_name_button)

        undo_remove_name_button = QPushButton("Namen entfernen rückgängig")
        # undo_remove_name_button.clicked.connect(self.on_show_info_clicked)
        button_layout.addWidget(undo_remove_name_button)

        self.save_image_button = QPushButton("Namen speichern")
        # self.save_image_button.clicked.connect(self.save_image_and_update_csv)
        button_layout.addWidget(self.save_image_button)

        # Add the buttons to the layout
        layout.addLayout(button_layout)




        # Label that shows the magnified patch
        self.magnify_label = QLabel("Magnified View")
        self.magnify_label.setFixedSize(450, 450)  # A fixed size for the magnifying preview
        self.magnify_label.setAlignment(Qt.AlignCenter)
        self.magnify_label.setStyleSheet("border: 1px solid black; background-color: #CCC;")
        self.magnify_label.setVisible(False)  # Hidden by default (until magnify is ON)
        self.hor_layout.addWidget(self.magnify_label, stretch=1)

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
        open_button.clicked.connect(lambda: self.open_image_dialog(from_tab='test', to_tab='test'), )

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
    # Basic Functions
    # --------------------------------------------------------------------------
    def image_resize(self, cv_img, max_pixel=800, from_tab='test', to_tab=''):

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
            max_dim = max_pixel  # Some default if the spinbox isn't present

        if hasattr(self, 'max_size_spin_files_tab') and from_tab == 'files':
            max_dim = self.max_size_spin_files_tab.value()
        else:
            max_dim = max_pixel

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

        return cv_img_rgb_display, disp_width, disp_height

    def resize_window(self, loc_x=800, loc_y=100, disp_width=800, disp_height=800):
        self.setGeometry(loc_x, loc_y, disp_width, disp_height)  # Set window location

    def fetch_top_level_tree_items(self, tree_widget):
        """
        Fetch all top-level items from the given QTreeWidget.
        """
        items = []
        for i in range(tree_widget.topLevelItemCount()):
            item = tree_widget.topLevelItem(i)
            path = item.data(0, Qt.UserRole)  # Get the full path from the item
            path = QDir.fromNativeSeparators(path)  # convert back slash to forward slash in directory string
            items.append(path)
        return items

    # --------------------------------------------------------------------------
    # Remove Names Functions
    # --------------------------------------------------------------------------
    def remove_name_mode(self):
        if self.remove_name_mode_status == False:
            self.remove_name_mode_status = True
            self.remove_name_button.setText("Namen entfernen: aktiviert") # change button text
            self.show_scanned_names() # Show the scanned names in the image
        else:
            self.remove_name_mode_status = False
            self.remove_name_button.setText("Namen entfernen") # change button text
            self.show_scanned_names()  # Show the scanned names in the image
        print(f"remove_name_mode status: {self.remove_name_mode_status}")
        self.find_csv_file_of_image(self.img_name) # Find the csv file of the image if available and update self.current_csv_path

        # open df of csv file
        self.edit_dataframe = pd.read_csv(self.current_csv_path)
        # print(self.edit_dataframe) # debugging

    def compare_bbox(self):
        # print("remove_name function") #debug
        if self.remove_name_mode_status == True:
            # Get the clicked coordinates
            for index, bbox in self.edit_dataframe['bbox'].items():
                # if bbox is a string then use ast.literal_eval to convert it to a list
                    if isinstance(bbox, str):
                        bbox = ast.literal_eval(bbox)# Use if bbox is from csv file

                    if self.orig_x >= bbox[0][0] and self.orig_x <= bbox[2][0] and self.orig_y >= bbox[0][1] and self.orig_y <= bbox[2][1]:
                        print(f"detected names clicked index: {index}") # debug
                        self.delete_name(index)

    def delete_name(self, index):
        deleted_csv_dir = f"{self.csv_edit}/{self.current_csv_path.split('/')[-1].split('.')[0]}_delete.csv"
        print(deleted_csv_dir) # debug
        # check if deleted_csv_dir exists
        if not os.path.exists(deleted_csv_dir):
            # create the directory if not exists
            # os.makedirs(deleted_csv_dir)
            # Create the new CSV file with headers
            with open(deleted_csv_dir, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(['bbox','Namen','Confidence Level','Bildname'])

        # Read all rows from source
        with open(self.current_csv_path, mode="r", newline="", encoding="utf-8") as src:
            reader = csv.reader(src)
            rows = list(reader)

            # Safety check: does the row exist?
        if index < 0 or index >= len(rows):
            # print(f"Row index {index} is out of range.")
            return

        # Extract the row we want to move
        row_to_move = rows.pop(index+1)

        with open(deleted_csv_dir, mode="a", newline="", encoding="utf-8") as dst:
            writer = csv.writer(dst)
            writer.writerow(row_to_move)

        # Move the index row to the deleted csv
        # with open(self.current_csv_path, mode="w", newline="", encoding="utf-8") as src:
        #     writer = csv.writer(src)
        #     writer.writerow(rows)

        # print(f"Moved row {index+1} from '{self.current_csv_path}' to '{deleted_csv_dir}'.") # debug


        # Remove the name from the dataframe
        self.edit_dataframe.drop(index, inplace=True)
        # Save the dataframe to csv
        self.edit_dataframe.to_csv(self.current_csv_path, index=False)
        print(f"deleted name index: {index}")

        # time.sleep(0.5)
        self.show_scanned_names()  # update the image with the new dataframe



    def eventFilter(self, source, event):
        """
        This method is called for every event on 'source' (label_image).
        We look for a MouseButtonPress, compute the click coordinates,
        and optionally map them back to the original image.
        """
        if source == self.label_edit_tab and event.type() == QEvent.MouseButtonPress:
            # Make sure we have a pixmap
            pixmap = self.label_edit_tab.pixmap()
            if pixmap is not None:
                # Where did the click happen (relative to label)?
                click_x = event.pos().x()
                click_y = event.pos().y()

                pixmap_w = pixmap.width()
                pixmap_h = pixmap.height()

                label_w = self.label_edit_tab.width()
                label_h = self.label_edit_tab.height()

                # If the image is centered, find offset
                offset_x = (label_w - pixmap_w) // 2
                offset_y = (label_h - pixmap_h) // 2

                # Check if within the displayed pixmap
                if (offset_x <= click_x < offset_x + pixmap_w and
                        offset_y <= click_y < offset_y + pixmap_h):
                    scaled_x = click_x - offset_x
                    scaled_y = click_y - offset_y

                    # Map to original
                    self.orig_x = int(scaled_x * (self.cv_img_rgb_original.shape[0] / self.cv_img_rgb_display.shape[0]))
                    self.orig_y = int(scaled_y * (self.cv_img_rgb_original.shape[1] / self.cv_img_rgb_display.shape[1]))

                    print(f"Clicked scaled=({scaled_x}, {scaled_y}), original=({self.orig_x}, {self.orig_y})")

                    self.compare_bbox() # Remove name function


            # Mark event as handled
            return True

        # Otherwise, default handling
        return super().eventFilter(source, event)


    # --------------------------------------------------------------------------
    # Image Data Functions
    # --------------------------------------------------------------------------
    def open_image_dialog(self, from_tab='test', to_tab=''):
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

        # print(f'img_name: {self.img_name}') # Debugging, image directory D:/Users/AGAM MUHAJIR/Documents/Projects/Smart_Kamera/10998509.jpg

        if self.img_name:
            # Use OpenCV to read the image (BGR format)
            cv_img = cv2.imread(self.img_name)

            if cv_img is not None:
                cv_img_rgb_display, disp_width, disp_height = self.image_resize(cv_img)


                #Store the scaled / unchanged result in the instance variable:
                self.cv_img_rgb_display = cv_img_rgb_display
                # Store the clean version
                self.cv_img_rgb_display_clean = cv_img_rgb_display.copy()

                # REsize the window
                self.resize_window(disp_width=disp_width, disp_height=disp_height)

                # Display the image in the label
                if to_tab == 'edit':
                    # self.label.setPixmap(pixmap)
                    self.show_image_in_label(cv_img_rgb_display, self.label_edit_tab)
                elif to_tab == 'test':
                    # self.image_label_test_tab.setPixmap(pixmap)
                    self.show_image_in_label(cv_img_rgb_display, self.image_label_test_tab)

                # Switch to the 'Edit Tab' automatically
                if to_tab == 'edit':
                    if self.jump_to_image:
                        self.central_widget.setCurrentIndex(1)
                elif to_tab == 'test':
                    self.central_widget.setCurrentIndex(2)

            else:
                QMessageBox.warning(self, "Error", "Failed to load image.")

        self.show_image_info_in_tree(self.img_name)  # Show image info in the tree widget
        if self.image_csv_finder(): # check if csv file exists
            self.show_scanned_names()  # Show the scanned names in the image

    def image_csv_finder(self):
        """
        Check if the csv file exists or not
        """
        # print(f'image_csv_finder running') # debugging
        # print(f'img_name: {self.img_name}') # Debugging

        # Get the filename from the full path
        file_name = self.img_name.split('/')[-1].split('.')[0] # Get the filename from the full path
        # print(f'file_name: {file_name}') # Debugging

        self.current_csv_path = f'{self.csv_path}/{file_name}.csv'  # update current csv path

        if os.path.exists(self.current_csv_path):
            return True
        else:
            print(f'csv file not found: {self.current_csv_path}') # Debugging
            return False

    def only_open_image(self, image_directory):
        """
        Only opens image
        no dialog box
        """

        # print(f'img_name: {self.img_name}') # Debugging

        self.img_name = image_directory

        if self.img_name:
            # Use OpenCV to read the image (BGR format)
            cv_img = cv2.imread(self.img_name)

            if cv_img is not None:
                cv_img_rgb_display, disp_width, disp_height = self.image_resize(cv_img, from_tab='files')

                # Store the scaled / unchanged result in the instance variable:
                self.cv_img_rgb_display = cv_img_rgb_display

                # Store the clean version
                self.cv_img_rgb_display_clean = cv_img_rgb_display.copy()

                # REsize the window
                self.resize_window(disp_width=disp_width, disp_height=disp_height)

                # Display the image in the label
                self.show_image_in_label(cv_img_rgb_display, self.label_edit_tab)

                # Switch to the 'Edit Tab' automatically
                if self.jump_to_image:
                    self.central_widget.setCurrentIndex(1)

            else:
                QMessageBox.warning(self, "Error", "Failed to load image.")

    def show_image_info_in_tree(self, image_directory):
        """
        Show image info in the tree widget, basically show image name in the image tree widget
        """
        filename = QDir.fromNativeSeparators(image_directory)  # convert back slash to forward slash in directory string
        filename = filename.split('/')[-1] # Get the filename from the full path
        # print(f'filename: {filename}') # Debugging
        item = QTreeWidgetItem([filename])
        # Store full path so we can open the image later
        item.setData(0, Qt.UserRole, image_directory)
        self.image_tree_widget.addTopLevelItem(item)

    def refresh_image_info_in_tree(self):
        """
        Refresh image info in the tree widget with the newly scanned csv files
        """
        #fetch all top level items
        folder_path_list = self.fetch_top_level_tree_items(self.image_tree_widget)
        # print(f'folder_path_list: {folder_path_list}') # Debugging

        # Clear the right tree before listing new files
        self.image_tree_widget.clear()

        # Loop through all items and add them to the tree widget
        for image in folder_path_list:
            #fetch the csv name of the image file
            csv = self.find_csv_file_of_image(image)

            # print(f'item: {item}') # Debugging
            item = QTreeWidgetItem([image, csv])
            # Store full path so we can open the image later
            item.setData(0, Qt.UserRole, item)
            self.image_tree_widget.addTopLevelItem(item)


    def open_image_folder(self):
        """
           Opens a folder selection dialog, lists all images in the RIGHT tree.
           Left tree is left empty for future use.
           """
        folder_path = QFileDialog.getExistingDirectory(self, "Select Folder", "")
        if not folder_path:
            return

        # Clear the right tree before listing new files
        self.image_tree_widget.clear()

        image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"}

        for filename in os.listdir(folder_path):
            ext = os.path.splitext(filename)[1].lower() # Get the file extension
            if ext in image_extensions:

                full_path = os.path.join(folder_path, filename) # Get full path
                self.show_image_info_in_tree(full_path) # Show image info in the tree widget
                '''
                # item = QTreeWidgetItem([filename])
                full_path = os.path.join(folder_path, filename) # Get full path
                # Store full path so we can open the image later
                # item.setData(0, Qt.UserRole, full_path)
                
                # self.image_tree_widget.addTopLevelItem(item)
                '''
        # temp = self.fetch_top_level_tree_items(self.image_tree_widget) # debug
        # print("fetch tree top level list: ", temp) # debug

    def image_tree_item_double_clicked(self, item, column):
        """
        User double-clicked an image name in the tree -> show it on the second tab.
        """
        # Retrieve the file path from the item
        file_path = item.data(0, Qt.UserRole)
        file_path = QDir.fromNativeSeparators(file_path) # convert back slash to forward slash in directory string
        # print(f'image tree double click file_path: {file_path}') # debugging
        self.img_name = file_path # update img_name with the selected image path
        # print(f'image tree double click self.img_name: {self.img_name}') # debugging

        # Find the csv file of the image if available
        # self.find_csv_file_of_image(file_path) # Redundant, delete later
        if self.image_csv_finder():  # check if csv file exists
            self.update_tree(self.current_csv_path)  # update tree with new data from scanned image
        else:
            self.update_tree('no_csv') # update tree with no csv file


        # clear any bold texts
        self.highlight_selected_item(item, column)

        # Switch to the image tab and display the selected image
        if self.jump_to_image:
            self.central_widget.setCurrentIndex(1)
        self.only_open_image(file_path)

    def highlight_selected_item(self, item, column):
        # clear any bold texts
        for i in range(self.image_tree_widget.topLevelItemCount()):
            text = self.image_tree_widget.topLevelItem(i)
            for j in range(item.columnCount()):
                font = text.font(j)
                font.setBold(False)
                text.setFont(j, font)
        # make selected text bold
        font = item.font(column)
        font.setBold(True)
        item.setFont(column, font)


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

    # --------------------------------------------------------------------------
    # Scanner Functions
    # --------------------------------------------------------------------------

    def activate_scanner(self):
        """
        Activate or deactivate the scanner.
        So that scanner module dont need to re-run for every image
        :return: None
        """
        # self.run_scanner_thread = threading.Thread(target=self.scanner_activated_thread)

        if self.scanner_active_status == False:
            self.activate_scanner_button.setText("Scanner deaktivieren") # Change button text
            self.scanner_active_status = True
            self.run_scanner_thread.start()
            print('Scanner activated')
        elif self.scanner_active_status == True:
            self.activate_scanner_button.setText("Scanner aktivieren")
            # Stop the scanner
            self.scanner_active_status = False
            self.run_scanner_thread.join()
            self.ocr_processor = None  # Clear the OCR processor
            print("Scanner deactivated")

    def scanner_activated_thread(self):
        """
        Activate or deactivate the scanner.
        So that scanner module dont need to re-run for every image
        show loading status
        :return: None
        """


        self.activate_scanner_button.setText("Scanner lädt")  # Just to show loading status
        modulename = 'OCRProcessor'
        if modulename not in sys.modules:
            from Modules.class_easyOCR_V1 import OCRProcessor
        # Initialize the OCR processor
        self.ocr_processor = OCRProcessor()
        self.activate_scanner_button.setText("Scanner deaktivieren")  # Change button text
        print('ocr_processor initialized')


    def scan_image(self, batch_scanning=False):
        print("Scan image clicked")
        print("self.img_name: ", self.img_name)
        # self.img_name = self.img_name.split("\\")[0]

        # Disable button to avoid multiple clicks
        self.scan_button.setEnabled(False)

        self.scan_thread = threading.Thread(target=self.scan_image_thread, args=(self.img_name, batch_scanning))
        self.scan_thread.start()

        # time.sleep(3) # Simulate a long-running task
        self.scan_thread.join()
        print('scan_thread finished')

        # Enable button to stop scanning
        self.scan_button.setEnabled(True)

    def show_scanned_names(self):
        # Get file name from the image path
        file_name = self.img_name.split('/')[-1].split('.')[0]
        # print(f'file_name: {file_name}') # debug

        self.current_csv_path = f'{self.csv_path}/{file_name}.csv' # update current csv path

        self.edit_dataframe = pd.read_csv(self.current_csv_path)
        # print("current edit_dataframe: ", self.edit_dataframe) # debug

        df_ocr_results = self.edit_dataframe

        # clear the image display
        self.cv_img_rgb_display = self.cv_img_rgb_display_clean.copy()  # Replace with clean version

        for bbox in df_ocr_results['bbox']:
            # if bbox is a string then use ast.literal_eval to convert it to a list
            if isinstance(bbox, str):
                bbox = ast.literal_eval(bbox)
            # bbox = ast.literal_eval(bbox) # Use if bbox is from csv file
            print(f'bbox values: {bbox}')
            scaled_ratio = self.cv_img_rgb_display.shape[0] / self.cv_img_rgb_original.shape[0] # match the ratio of the original image to the displayed image

            cv2.rectangle(self.cv_img_rgb_display,
                          (int((bbox[0][0])*scaled_ratio), int((bbox[0][1])*scaled_ratio)),
                          (int((bbox[2][0])*scaled_ratio), int((bbox[2][1])*scaled_ratio)),
                          (0, 255, 0), 1)

        self.show_image_in_label(self.cv_img_rgb_display, self.label_edit_tab)

        if self.image_csv_finder():  # check if csv file exists
            self.update_tree(self.current_csv_path) #update tree with new data from scanned image




    def scan_image_thread(self, img_name_local, batch_scanning=False):
        # from Modules.class_easyOCR_V1 import OCRProcessor
        # # Initialize the OCR processor
        # ocr_processor = OCRProcessor()
        # Perform OCR on the given image
        df_ocr_results = self.ocr_processor.ocr(img_name_local)
        print(df_ocr_results.head(5))

        # save_path = '../csv_speichern'
        save_path = 'csv_speichern'
        # Save the OCR results to a CSV file
        self.ocr_processor.save_to_csv(df_ocr_results, img_name_local, save_path)

        if not batch_scanning:
            self.show_scanned_names() # update image with scanned names



        # Simulate a long-running task
        # time.sleep(3)
        print("Scan image thread finished")

    def scan_all_image(self):
        """
        Scan all images in the selected folder
        """
        # Get the selected folder path from the image tree widget
        folder_path_list = self.fetch_top_level_tree_items(self.image_tree_widget)
        print(f'folder_path: {folder_path_list}') # debug

        for folder_path in folder_path_list:
            # insert into self.img_name
            self.img_name = folder_path
            # Run scan_image_thread
            self.scan_image(batch_scanning=True)


    # --------------------------------------------------------------------------
    # CSV Functions
    # --------------------------------------------------------------------------
    def open_csv_dialog(self):
        """
        Open a file dialog to pick a CSV file, then populate the QTreeWidget
        with the CSV contents.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        if not file_path:
            return  # User canceled or closed the dialog

        # Store the path so we can save changes back to the same file
        self.current_csv_path = file_path

        self.update_tree(self.current_csv_path)



    def update_tree(self, file_path):
        """
        If the file path is 'no_csv', clear the tree widget.
        Else, read the CSV file and populate the tree widget.
        """
        if file_path == 'no_csv':
            self.csv_tree_widget.clear()
            return

        # Read the CSV file
        rows = []
        with open(file_path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        if not rows:
            return  # CSV was empty

        # NEW: Clear existing items before adding new CSV rows
        self.csv_tree_widget.clear()

        # If the CSV has a header row, let's skip it or do something with it
        # For example, if the first line is a header, you can do:
        # header = rows[0]
        # Create custom header
        header = ['bbox', 'Namen', 'Confidence Level', 'Bildname']
        self.csv_tree_widget.setHeaderLabels(header)
        # First row will always be after the header
        rows = rows[1:]
        #
        # But if your CSV data is purely rows with the same 3 columns,
        # you can just treat them all as data items.

        # Insert each CSV row as a new top-level item
        for row_data in rows:
            # If the row doesn't have exactly 3 columns, you may need to pad or slice
            # e.g., row_data = row_data[:3] or something like that
            while len(row_data) < 4:
                row_data.append("")  # pad to ensure at least 3 columns
            # Create an item from this row
            item = QTreeWidgetItem(row_data[:4])  # take exactly 3 columns
            item.setFlags(item.flags() | Qt.ItemIsEditable)

            # We add it as a top-level item, but you could also place it under some root
            self.csv_tree_widget.addTopLevelItem(item)

    def populate_tree_from_dict(self):
        """
        Populate the QTreeWidget from a hard-coded dictionary (example_dict).
        Each key becomes a 'root' item; each sub-list becomes child items.
        """
        example_dict = {
            "Briefkaesten_beispeil": [
                ["ID Nummer 1", "Max", "[123],[456],[789],[101]"],
                ["ID Nummer 2", "Mustermann", "[123],[456],[789],[101]"]
            ],
            "Briefkaesten_beispeil_2": [
                ["ID Nummer 2", "Mustermann", "[123],[456],[789],[101]"]
            ]
        }

        # Clear existing items (in case you're re-calling this)
        self.csv_tree_widget.clear()

        # Re-set column headers (optional, only if changed)
        self.csv_tree_widget.setHeaderLabels(["Bildname", "Namen", "Bbox"])

        for file_name, data in example_dict.items():
            root_item = QTreeWidgetItem([file_name, "", ""])
            # Make the root item editable:
            root_item.setFlags(root_item.flags() | Qt.ItemIsEditable)
            self.csv_tree_widget.addTopLevelItem(root_item)

            for row in data:
                child_item = QTreeWidgetItem(row)
                # Make the child item editable:
                child_item.setFlags(child_item.flags() | Qt.ItemIsEditable)
                root_item.addChild(child_item)

    def save_csv_dialog(self):
        """
        Write the current data from the QTreeWidget back to self.current_csv_path.
        """
        # If no file has been opened yet, prompt user or do nothing
        if not self.current_csv_path:
            # (Optional) Let the user pick a location to save
            # In that case, you'd do something like:
            # self.current_csv_path, _ = QFileDialog.getSaveFileName(...)
            # if not self.current_csv_path:
            #     return
            print("No file path available to save.")
            return

        #check if the csv_speichern directory exists
        if not os.path.exists(self.csv_path):
            os.makedirs(self.csv_path)

        # Gather data from each top-level item
        num_top_items = self.csv_tree_widget.topLevelItemCount()
        num_columns = self.csv_tree_widget.columnCount()

        data_rows = []
        for i in range(num_top_items):
            item = self.csv_tree_widget.topLevelItem(i)
            row_data = []
            for col in range(num_columns):
                row_data.append(item.text(col))
            data_rows.append(row_data)

        # check header
        expected_header = ['bbox','Namen','Confidence Level','Bildname']
        if not data_rows or data_rows[0] != expected_header:
            # Insert the header at the beginning
            data_rows.insert(0, expected_header)

        # Write CSV
        with open(self.current_csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerows(data_rows)

        # print(f"Saved changes back to: {self.current_csv_path}") # Debugging

    def find_csv_file_of_image(self, image_path):
        file_path = image_path
        # Find the csv file of the image if available
        csv_folder = 'csv_speichern'
        csv_file_name = file_path.split('/')[-1].split('.')[0] + '.csv'  # Get the csv file name

        # check if the csv file exists
        if os.path.exists(f'{csv_folder}/{csv_file_name}'):
            # If the csv file exists, open it
            self.current_csv_path = f'{csv_folder}/{csv_file_name}'
            # print(f'csv file exists: {self.current_csv_path}')  # debugging



if __name__ == "__main__":
    app = QApplication(sys.argv)


    window = MainWindow()# Change to your video source
    window.show()
    sys.exit(app.exec_())
