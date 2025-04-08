__author__ = 'mkv-aql'
import pandas as pd

class CSVHandler:
    """
    Class to handle CSV file operations.
    """
    def __init__(self, file_path):
        """
        Initialize the CSVHandler with the path to the CSV file.

        :param file_path: Path to the CSV file.
        """
        self.file_path = file_path

    def read_csv(self):
        """
        Read the CSV file and return its content as a DataFrame.

        :return: DataFrame containing the CSV data.
        """
        try:
            df = pd.read_csv(self.file_path)
            return df
        except FileNotFoundError:
            print(f"File not found: {self.file_path}")
            return None