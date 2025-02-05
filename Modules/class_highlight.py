import cv2
import numpy as np

class RectangleSelector:
    def __init__(self, image, width, height):
        # For rescaling later
        self.orignal_image = image
        self.original_width, self.original_height = image.shape[:2]

        # Resize the image for display
        self.image = cv2.resize(image, (width, height))
        #self.image = image # Uncomment this line if you want to use the original image size
        self.width = width
        self.height = height

        # Create a copy of the image to draw rectangles on
        self.frame = self.image.copy()
        self.drawing = False
        self.ix, self.iy = -1, -1
        self.rectangles = []
        self.undo_stack = []
        self.window_name = 'Image'

        # Calculate scale factors
        self.scale_x = self.original_width / self.width
        self.scale_y = self.original_height / self.height

        # Set up the mouse callback
        cv2.namedWindow(self.window_name)
        cv2.setMouseCallback(self.window_name, self.draw_rectangle)

    def draw_rectangle(self, event, x, y, flags, param):
        # Adjust x, y coordinates for the resized image
        x = int(x * (self.image.shape[1] / self.width))
        y = int(y * (self.image.shape[0] / self.height))

        if event == cv2.EVENT_LBUTTONDOWN:
            self.drawing = True
            self.ix, self.iy = x, y

        elif event == cv2.EVENT_MOUSEMOVE:
            if self.drawing:
                # Create a temporary frame to display the rectangle
                temp_frame = self.frame.copy()
                cv2.rectangle(temp_frame, (self.ix, self.iy), (x, y), (0, 255, 0), 2)
                cv2.imshow(self.window_name, temp_frame)

        elif event == cv2.EVENT_LBUTTONUP:
            self.drawing = False
            cv2.rectangle(self.frame, (self.ix, self.iy), (x, y), (0, 255, 0), 2)

            # Convert the coordinates back to the original image size
            original_top_left = (int(self.ix * self.scale_x), int(self.iy * self.scale_y))
            original_bottom_right = (int(x * self.scale_x), int(y * self.scale_y))

            # self.rectangles.append(((self.ix, self.iy), (x, y)))
            # self.undo_stack.append(((self.ix, self.iy), (x, y)))
            self.rectangles.append((original_top_left, original_bottom_right))
            self.undo_stack.append((original_top_left, original_bottom_right))
            cv2.imshow(self.window_name, self.frame)

    def undo_last_rectangle(self):
        if self.undo_stack:
            self.undo_stack.pop()  # Remove the last rectangle from the undo stack
            self.redraw_frame()

    def redraw_frame(self):
        self.frame = self.image.copy()  # Reset the frame to the original image
        for rect in self.undo_stack:
            cv2.rectangle(self.frame, rect[0], rect[1], (0, 255, 0), 2)
        cv2.imshow(self.window_name, self.frame)

    def run(self):
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('u'):  # Press 'u' to undo the last rectangle
                self.undo_last_rectangle()
            elif cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
                break

        cv2.destroyAllWindows()
        return self.rectangles

# Usage example
if __name__ == "__main__":
    # Load an image or create a blank one
    image = cv2.imread('your_image.jpg')  # Replace with your image path
    # If you want a blank image, uncomment the line below:
    # image = np.zeros((500, 500, 3), dtype=np.uint8)

    selector = RectangleSelector(image)
    highlighted_areas = selector.run()
    print("Highlighted areas:", highlighted_areas)
