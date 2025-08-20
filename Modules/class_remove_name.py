__author__ = 'mkv-aql'

class RemoveName:
    """
    Class to remove the 'Namen' column from a DataFrame.
    """

    def __init__(self, df):
        """
        Initialize with a DataFrame.

        :param df: The DataFrame to process.
        """
        self.df = df

    def remove_name_column(self):
        """
        Remove the 'Namen' column from the DataFrame.
        """
        if 'Namen' in self.df.columns:
            self.df.drop(columns=['Namen'], inplace=True)
            print("Removed 'Namen' column.")
        else:
            print("'Namen' column not found.")