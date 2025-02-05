__author__ = 'mkv-aql'

import ast
import easyocr
import cv2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Set global Pandas and NumPy options
pd.set_option('display.max_columns', None)  # Display all columns
np.set_printoptions(linewidth=200, precision=4)


class OCRProcessor:
    def __init__(self, language='de', gpu=True, recog_network='latin_g2'):
        """
        Initialize the OCR processor.

        :param language: The language for the OCR model.
        :param gpu: Whether to use GPU for OCR processing.
        :param recog_network: The recognition network to use (default is 'latin_g2').
        """
        self.reader = easyocr.Reader([language], gpu=gpu, recog_network=recog_network)

    def ocr(self, image_path):
        """
        Perform OCR on the given image.

        :param image_path: Path to the image file.
        :return: A DataFrame containing OCR results (bbox, Namen, Confidence Level).
        """
        image = cv2.imread(image_path)
        ocr_results = self.reader.readtext(image, contrast_ths=0.05, adjust_contrast=0.7, text_threshold=0.8,
                                           low_text=0.4)
        df_ocr_results = pd.DataFrame(ocr_results, columns=['bbox', 'Namen', 'Confidence Level'])
        return df_ocr_results

    def save_to_csv(self, df_ocr_results, file_name):
        """
        Save the OCR results DataFrame to a CSV file.

        :param df_ocr_results: The OCR results DataFrame.
        :param file_name: The name for the CSV file (without extension).
        """
        csv_name = f'{file_name}.csv'
        df_ocr_results.to_csv(csv_name, index=False)
        print(f'Saved to {csv_name}')

