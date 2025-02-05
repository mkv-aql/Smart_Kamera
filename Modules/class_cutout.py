import cv2
import os


class ImageCutoutSaver:
    def __init__(self, image_path, output_folder='temp_cutouts'):
        self.image_path = image_path
        self.output_folder = output_folder
        self.image = cv2.imread(self.image_path)

        # Check if the image was loaded successfully
        if self.image is None:
            raise ValueError(f"Image not found or unable to load: {self.image_path}")

        # Create the output folder if it doesn't exist
        os.makedirs(self.output_folder, exist_ok=True)

    def save_cutouts(self, coordinates, file_name):
        for i, (top_left, bottom_right) in enumerate(coordinates):
            # Define the cut-out region using the coordinates
            x1, y1 = top_left
            x2, y2 = bottom_right

            # Ensure coordinates are within the image bounds
            x1, x2 = max(x1, 0), min(x2, self.image.shape[1])
            y1, y2 = max(y1, 0), min(y2, self.image.shape[0])

            # Skip if the coordinates are the same or if the region is invalid
            if (x1 >= x2) or (y1 >= y2):
                print(f"Skipping invalid cutout for index {i}: {top_left}, {bottom_right}")
                continue

            # Cut the region from the image
            cutout = self.image[y1:y2, x1:x2]

            # Define the output file name
            output_file = os.path.join(self.output_folder, f'{file_name}_{i + 1}.png')

            # Save the cut-out image
            cv2.imwrite(output_file, cutout)
            print(f'Saved: {output_file}')


# Example usage
if __name__ == "__main__":
    # Define the image path
    img_path = 'image_files/captured_test.jpg'  # Replace with your actual image path

    # Example coordinates
    coordinates = [((279, 110), (279, 110)), ((128, 90), (359, 246)),
                   ((209, 193), (401, 385)), ((134, 219), (353, 391)),
                   ((120, 115), (384, 286)), ((339, 81), (570, 260))]

    # Create an instance of ImageCutoutSaver
    cutout_saver = ImageCutoutSaver(img_path)

    # Save the cutouts
    cutout_saver.save_cutouts(coordinates)
