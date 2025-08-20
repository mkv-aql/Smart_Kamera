import os
# import nothing
import cv2
import pandas as pd
import ast
from Modules.class_highlight import RectangleSelector as rs #For highlighting module
from Modules.class_cutout import ImageCutoutSaver as ics #For cutout module
from Modules.class_entry_input_2 import CsvEditor as ei #For entry input module
# from Modules.class_easyOCR_V1 import OCRProcessor # for ocr detection, Moved to run_detection() function for faster app
import tkinter as tk

# Window size for ratio
########################################################################################################################
# Get screen size and font size
screen_width = 1920 - (1920 * 0.02); screen_width = int(screen_width)
screen_height = 1080 - (1080 * 0.02); screen_height = int(screen_height)
font_size = 3 # Original 1
font_thickness = 3 # Original 1
button_text_y_offset = 100 # Originally 30
button_text_x_offset = 10 # Originally 10
button_gaps_distance = 40

#Load csv
########################################################################################################################
# df_capture = pd.read_csv('capture_test.csv')
csv_dir = 'csv_bearbeiten'
csv_path = 'csv_bearbeiten/Briefkaesten.csv'
df_capture = pd.read_csv(csv_path)
df_capture_delete = pd.DataFrame(columns=['bbox', 'Namen'])

# img_path = 'captured_test.jpg'
img_path = 'bilder/Briefkaesten.jpg'
img_name = os.path.splitext(os.path.basename(img_path))[0] #Remove extension


#Function to convert the bbox string to a list of integers
def parse_bbox(bbox_str):

    if isinstance(bbox_str, str):
        # Remove the np.int32() parts and evaluate the string safely
        cleaned_str = bbox_str.replace('np.int32(', '').replace(')', '')
        cleaned_str = cleaned_str.replace('np.float64(', '').replace(')', '')
        return ast.literal_eval(cleaned_str)
    return bbox_str


# Function to safely convert bbox values to integer lists
def safe_convert_bbox_to_integers(bbox_str):
    try:
        # If the value is a string representation of a list, convert it
        if isinstance(bbox_str, str):
            bbox_list = ast.literal_eval(bbox_str)  # Convert the string representation to a list
        else:
            bbox_list = bbox_str  # If it's already a list, no conversion needed

        # Round the float values to integers and convert any negative values to 0
        #bbox_list_int = [[int(round(coord)) for coord in point] for point in bbox_list]
        bbox_list_int = [[max(0, int(round(coord))) for coord in point] for point in bbox_list]
        return bbox_list_int

    except (ValueError, SyntaxError):
        # Return the original value if there's an error in conversion
        print(f"Error processing bbox: {bbox_str}")
        return bbox_str

# CSV setup function
def csv_setup():
    global df_capture
    # Apply the function to the bbox column
    df_capture['bbox'] = df_capture['bbox'].apply(parse_bbox)
    df_capture['bbox'] = df_capture['bbox'].apply(safe_convert_bbox_to_integers)
    print(f'size of df_capture: {df_capture.size}')

    # Now, df['bbox'] contains lists of integer coordinates
    # print(df_capture['bbox'].tolist()) # List of lists of integers
    print(f'bbox:\n{df_capture["bbox"]}')

    # Remove Bildname and confidence level columns
    # df_capture.drop(columns=['Bildname', 'Confidence Level'], inplace=True)q
    try:
        df_capture.drop(columns=['Confidence Level'], inplace=True)
        df_capture.drop(columns=['Bildname'], inplace=True)
    except:
        pass
    print(f'bbox and Namen only: \n{df_capture}')

########################################################################################################################
# System Status
state = 0 # 0 = start, 1 = Remove, 2 = Edit, 3 = Save, 4 = Manual Input, 5 = Redetect


#Button functions
def mouse_callback(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        print(f'x: {x}, y: {y}')
        global state

        match state:
            case 0:
                for btn, pos in button_positions_0.items():
                    if pos[0] < x < pos[0] + button_width and pos[1] < y < pos[1] + button_height:
                        print(f'btn = {btn}')
                        button_callbacks_0[btn]() # () for passing arguments
                        print(f'State: {state}')

            case 1:
                for btn, pos in button_positions_1.items():
                    if pos[0] < x < pos[0] + button_width and pos[1] < y < pos[1] + button_height:
                        print(f'btn = {btn}')
                        button_callbacks_1[btn]() # () for passing arguments
                        print(f'State: {state}')

                for index, row in df_capture.iterrows():
                    (top_left, top_right, bottom_right, bottom_left) = row['bbox'][0], row['bbox'][1], row['bbox'][2], row['bbox'][3]
                    button_top_left_name = (top_left[0] - 10, top_left[1] - 10)
                    button_bottom_right_name = (bottom_right[0] + 10, bottom_right[1] + 10)
                    # print(f'\nbutton_top_left_name: {button_top_left_name}')
                    # print(f'\nbutton_bottom_right_name: {button_bottom_right_name}')
                    if button_top_left_name[0] < x < button_bottom_right_name[0] and button_top_left_name[1] < y < button_bottom_right_name[1]:
                        print(f'Index: {index} clicked')
                        #remove_index(index)
                        button_callbacks_1_func['Delete'](index)
                        print(f'State: {state}')

                    elif btn == None:
                        print(f'Index not found')
                        continue

                    else:
                        continue
                    break

            case 2:
                global img_name
                for btn, pos in button_positions_2.items():
                    if pos[0] < x < pos[0] + button_width and pos[1] < y < pos[1] + button_height:
                        print(f'btn = {btn}')
                        if btn == 'Manuelle Erkennung':
                            button_callbacks_2[btn](img_name)
                        else:
                            button_callbacks_2[btn]()  # () for passing arguments
                            print(f'State: {state}')

            case 3:
                for btn, pos in button_positions_3.items():
                    if pos[0] < x < pos[0] + button_width and pos[1] < y < pos[1] + button_height:
                        print(f'btn = {btn}')
                        button_callbacks_3[btn]()  # () for passing arguments
                        print(f'State: {state}')



######################################################################################################################## DRAW FUNCTION
def draw_button_0(frame):
    for button, pos in button_positions_0.items():
        cv2.rectangle(frame, pos, (pos[0] + button_width, pos[1] + button_height), (200, 200, 200), -1)
        if button == 'Manuelle Eingabe':
            cv2.putText(frame, 'Manuelle', (pos[0] + button_text_x_offset, pos[1] + button_text_y_offset), cv2.FONT_HERSHEY_SIMPLEX, font_size, (0, 0, 0), font_thickness)
            cv2.putText(frame, 'Eingabe', (pos[0] + button_text_x_offset, pos[1] + button_text_y_offset + 80), cv2.FONT_HERSHEY_SIMPLEX, font_size, (0, 0, 0), font_thickness)
        else:
            cv2.putText(frame, button, (pos[0] + button_text_x_offset, pos[1] + button_text_y_offset), cv2.FONT_HERSHEY_SIMPLEX, font_size, (0, 0, 0), font_thickness)

def draw_button_1(frame):
    for button, pos in button_positions_1.items():
        cv2.rectangle(frame, pos, (pos[0] + button_width, pos[1] + button_height), (200, 200, 200), -1)
        cv2.putText(frame, button, (pos[0] + button_text_x_offset, pos[1] + button_text_y_offset), cv2.FONT_HERSHEY_SIMPLEX, font_size, (0, 0, 0), font_thickness)

def draw_button_2(frame):
    for button, pos in button_positions_2.items():
        cv2.rectangle(frame, pos, (pos[0] + button_width, pos[1] + button_height), (200, 200, 200), -1)
        cv2.putText(frame, button, (pos[0] + button_text_x_offset, pos[1] + button_text_y_offset), cv2.FONT_HERSHEY_SIMPLEX, font_size, (0, 0, 0), font_thickness)

def draw_button_3(frame):
    for button, pos in button_positions_3.items():
        cv2.rectangle(frame, pos, (pos[0] + button_width, pos[1] + button_height), (200, 200, 200), -1)
        cv2.putText(frame, button, (pos[0] + button_text_x_offset, pos[1] + button_text_y_offset), cv2.FONT_HERSHEY_SIMPLEX, font_size, (0, 0, 0), font_thickness)

######################################################################################################################## BUTTON FUNCTIONS
def delete_index(index):
    global df_capture_delete
    global df_capture
    # add to df_capture_delete
    df_capture_delete = df_capture_delete._append(df_capture.loc[index], ignore_index=True)
    df_capture.drop(index, inplace=True)
    # print(f'Index {index} removed')
    # print(f'df_capture_delete: {df_capture_delete}')
    # print(f'df_capture: {df_capture}')

def undo_delete():
    global df_capture_delete
    global df_capture
    # add the last row of df_capture_delete to df_capture
    try:
        index = df_capture_delete.index[-1]
    except IndexError:
        print('No index to undo')
        return
    df_capture = df_capture._append(df_capture_delete.loc[index], ignore_index=True)
    df_capture_delete.drop(index, inplace=True)
    # print(f'Index {index} Reinserted')
    # print(f'df_capture_delete: {df_capture_delete}')
    # print(f'df_capture: {df_capture}')

def save_csv():
    global df_capture
    df_capture.reset_index(drop=True, inplace=True)# reset the index
    df_capture.to_csv('csv_files/capture_test_final.csv')
    print(f'Save button clicked')

def redetect_mode():
    global state
    state = 2
    print('Redetect button clicked')

def manual_input_mode():
    global state
    state = 3
    root = tk.Tk()
    ei(root, csv_path)
    root.mainloop()
    print('Manual Input button clicked')

def start_mode():
    print('Start button clicked')
    global state
    state = 0

def remove_mode():
    print('Remove mode button clicked')
    global state
    state = 1

def update():
    global df_capture
    df_capture = pd.read_csv(csv_path)
    csv_setup() # Re setup
    print('Update button clicked')

def save_chosen():
    global df_capture
    df_capture.reset_index(drop=True, inplace=True)  # reset the index
    df_capture.to_csv(csv_path, index=False)
    print('Save chosen button clicked')

def run_detection():
    from Modules.class_easyOCR_V1 import OCRProcessor
    global img_path, df_capture, csv_dir
    #img_path = cv2.imread(img_path)
    ocr_processor = OCRProcessor(language='de', gpu=True, recog_network='latin_g2')
    # Perform OCR on the image
    df_capture = ocr_processor.ocr(img_path)
    # Save the results to a CSV (file name without extension)
    file_name = img_path.split('/')[-1].split('.')[0]
    path_name = f"{csv_dir}/{file_name}"
    ocr_processor.save_to_csv(df_capture, path_name)
    # Refresh
    df_capture = pd.read_csv(csv_path) # Re read csv
    csv_setup() # Re setup
    print('Run detection button clicked')

def manual_detection(frame_name):
    global img_path, df_capture, csv_dir, screen_width, screen_height
    file_name = img_path.split('/')[-1].split('.')[0]
    # image = cv2.imread(f'{frame_name}_clean.jpg')
    image = cv2.imread(img_path)
    selector = rs(image, screen_width, screen_height)
    highlighted_areas = selector.run()
    # Save the highlighted areas to a file csv file
    with open('temp_cutouts\df_coordinates.csv', 'w') as f:
        for area in highlighted_areas:
            f.write(f'{area}\n')
    print("Highlighted areas:", highlighted_areas)
    print('Manual detection button clicked')
    cutout_saver = ics(img_path) # Create an instance of ImageCutoutSaver
    cutout_saver.save_cutouts(highlighted_areas, file_name) # Save the cutouts

    for filename in os.listdir('temp_cutouts'):
        if filename.startswith(f'{file_name}_') and filename.endswith('.png'):
            # Process the file
            print(f"Processing file: {filename}")
            run_detection_2(f'temp_cutouts/{filename}')

def run_detection_2(img_path):
    from Modules.class_easyOCR_V1 import OCRProcessor
    global df_capture, csv_dir
    #img_path = cv2.imread(img_path)
    ocr_processor = OCRProcessor(language='de', gpu=True, recog_network='latin_g2')
    # Perform OCR on the image
    df_capture = ocr_processor.ocr(img_path)
    # Save the results to a CSV (file name without extension)
    file_name = img_path.split('/')[-1].split('.')[0]
    path_name = f"{csv_dir}/{file_name}"
    ocr_processor.save_to_csv(df_capture, path_name)
    # Refresh
    df_capture = pd.read_csv(csv_path) # Re read csv
    csv_setup() # Re setup



######################################################################################################################## Button size
# Button Coordinates:
    #Save button corrdinates
ratio_size_h = 0.2
ratio_size_w = 0.35
button_height = ratio_size_h * screen_height # 324
button_width = ratio_size_w * screen_width # 576
button_height = int(button_height)
button_width = int(button_width)
######################################################################################################################## 0
button_positions_0 = {
    'Speichern': (0, 0),
    'Manuelle Eingabe': (button_width + button_gaps_distance, 0), # Originally 102, 0
    'Neu erkennen': ((button_width + button_gaps_distance)*2, 0), # Originally 204, 0
    'Loeschen': ((button_width + button_gaps_distance)*3, 0) # Originally 306, 0
}

button_callbacks_0 = {
    'Speichern': save_csv,
    'Manuelle Eingabe': manual_input_mode,
    'Neu erkennen': redetect_mode,
    'Loeschen': remove_mode
}

######################################################################################################################## 1
button_positions_1 = {
    'Startseite': (0, 0),
    'Save Chosen': (button_width + button_gaps_distance, 0),
    'Undo Delete': ((button_width + button_gaps_distance)*2, 0)
}

button_callbacks_1 = {
    'Startseite': start_mode,
    'Save Chosen': save_chosen,
    'Undo Delete': undo_delete
}

button_callbacks_1_func = {
    'Delete': delete_index
}

######################################################################################################################## 2
button_positions_2 = {
    'Startseite': (0, 0),
    'Run Detection': (button_width + button_gaps_distance, 0),
    'Manuelle Erkennung': ((button_width + button_gaps_distance)*2, 0)
}

button_callbacks_2 = {
    'Startseite': start_mode,
    'Run Detection': run_detection,
    'Manuelle Erkennung': manual_detection
}

######################################################################################################################## 3
button_positions_3 = {
    'Startseite': (0, 0),
    'Aktualisieren': (button_width + button_gaps_distance, 0)
}

button_callbacks_3 = {
    'Startseite': start_mode,
    'Aktualisieren': update
}

button_callbacks_3_func = {
    'Delete': delete_index
}

######################################################################################################################## RUN
csv_setup() # csv setup
while True:

    img = cv2.imread(img_path)

    for index, row in df_capture.iterrows():
        (top_left, top_right, bottom_right, bottom_left) = row['bbox'][0], row['bbox'][1], row['bbox'][2], row['bbox'][3]
        cv2.rectangle(img, top_left, bottom_right, (0, 0, 255), 3)
        cv2.putText(img, row['Namen'], top_left, cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 0, 255), 2, cv2.LINE_AA)

    # Draw buttons based on current state
    if state == 0:
        draw_button_0(img)
    elif state == 1:
        draw_button_1(img)
    elif state == 2:
        draw_button_2(img)
    elif state == 3:
        draw_button_3(img)
    else:
        pass

    # Display the frame to fit screen
    cv2.namedWindow('edit', cv2.WINDOW_NORMAL)
    cv2.resizeWindow('edit', screen_width, screen_height)
    cv2.imshow('edit', img)

    # Set mouse function
    cv2.setMouseCallback('edit', mouse_callback)
    # cv2.setMouseCallback('edit', mouse_callback_save)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

