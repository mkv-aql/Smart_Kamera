# csv_editor.py
import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd


class CsvEditor:
    def __init__(self, root, csv_file_path=None):
        self.root = root
        self.root.title("CSV Editor")

        self.csv_data = None
        self.csv_file_path = csv_file_path

        # Create UI components
        self.frame = tk.Frame(self.root)
        self.frame.pack(pady=10)

        # self.load_button = tk.Button(self.frame, text="Load CSV", command=self.load_csv)
        # self.load_button.pack(side=tk.LEFT, padx=5)

        self.clean_names = tk.Button(self.frame, text="Clean Names", command=self.clean_csv)
        self.clean_names.pack(side=tk.LEFT, padx=5)

        self.save_button = tk.Button(self.frame, text="Save CSV", command=self.save_csv)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.add_button = tk.Button(self.frame, text="Add Name", command=self.add_name)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(self.frame, text="Delete Name", command=self.delete_name)
        self.delete_button.pack(side=tk.LEFT, padx=5)  # Added a button to delete names

        self.name_label = tk.Label(self.frame, text="Enter Name:")
        self.name_label.pack(side=tk.LEFT, padx=5)

        self.name_entry = tk.Entry(self.frame)
        self.name_entry.pack(side=tk.LEFT, padx=5)

        self.listbox = tk.Listbox(self.root, width=50, height=15)
        self.listbox.pack(pady=10)

        # If a CSV file path is provided, load it immediately
        if self.csv_file_path:
            self.load_csv(self.csv_file_path)


    def clean_csv(self):
        print("clean_csv clicked")
        if self.csv_data is not None:
            try:
                #self.csv_data = pd.read_csv(file_path)
                self.csv_data['Namen'] = self.csv_data['Namen'].str.strip()  # Remove leading/trailing spaces
                self.csv_data['Namen'] = self.csv_data['Namen'].str.title()  # Capitalize first letter
                self.csv_data.drop_duplicates(subset=['Namen'], keep='first', inplace=True)  # Remove duplicates
                self.csv_data.reset_index(drop=True, inplace=True)  # Reset the index
                self.csv_data['Namen'] = self.csv_data['Namen'].str.replace(r'[0-9]', '', regex=True)  # Remove numbers
                self.csv_data['Namen'] = self.csv_data['Namen'].str.replace(r'[^\w\s]', '', regex=True)  # Remove special characters
                # Remove rows with empty names
                self.csv_data = self.csv_data.explode('Namen')
                self.csv_data = self.csv_data[self.csv_data['Namen'].str.strip() != '']
                # Remove rows with only single letters
                self.csv_data = self.csv_data[self.csv_data['Namen'].str.len() > 1]
                print('Test')
            except Exception as e:
                messagebox.showerror("Error", f"Failed to clean CSV file: {e}")
        self.save_csv()
        self.load_csv(self.csv_file_path) #Reload the cleaned csv

    def load_csv(self, file_path=None):
        if file_path is None:
            file_path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])

        if file_path:
            try:
                self.csv_data = pd.read_csv(file_path)
                self.listbox.delete(0, tk.END)  # Clear previous entries
                for index, row in self.csv_data.iterrows():
                    # Show index and current names
                    self.listbox.insert(tk.END, f"{index}: {row['Namen']}")
                self.csv_file_path = file_path  # Set file path if loaded via dialog
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load CSV file: {e}")

    def save_csv(self):
        if self.csv_data is not None:
            # Save the updated DataFrame back to the original CSV or ask for a save path if not provided
            if self.csv_file_path:
                save_path = self.csv_file_path
            else:
                save_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])

            if save_path:
                self.csv_data.to_csv(save_path, index=False)
                messagebox.showinfo("Success", f"CSV file saved successfully: {save_path}")

    def add_name(self):
        if self.csv_data is not None:
            new_name = self.name_entry.get()
            if not new_name:
                messagebox.showwarning("Warning", "Please enter a name before adding.")
                return

            # Add the new name to the DataFrame
            new_index = len(self.csv_data)  # Get the next index
            self.csv_data.loc[new_index] = [None, new_name, 0]  # Add a new row

            # Clear the entry and refresh the listbox
            self.name_entry.delete(0, tk.END)
            self.listbox.delete(0, tk.END)
            for index, row in self.csv_data.iterrows():
                self.listbox.insert(tk.END, f"{index}: {row['Namen']}")

            #messagebox.showinfo("Success", f"Added new name: {new_name}")

    def delete_name(self):
        if self.csv_data is not None:
            # Get the selected item from the listbox
            selected_index = self.listbox.curselection()

            if not selected_index:
                messagebox.showwarning("Warning", "Please select a name to delete.")
                return

            # Get the corresponding index in the DataFrame
            selected_name = self.listbox.get(selected_index).split(": ")[1]  # Get name from Listbox

            # Remove the row with the selected name from the DataFrame
            self.csv_data = self.csv_data[self.csv_data['Namen'] != selected_name]

            # Refresh the listbox
            self.listbox.delete(0, tk.END)
            for index, row in self.csv_data.iterrows():
                self.listbox.insert(tk.END, f"{index}: {row['Namen']}")
