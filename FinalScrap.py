import sys
import os
import numpy as np
# print("Current working directory: ", os.getcwd())
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton,
    QProgressBar, QTableWidget, QTableWidgetItem, QWidget,
    QHBoxLayout, QHeaderView, QLineEdit, QComboBox, QLabel,
    QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options # for page load strategy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
class ScraperThread(QThread):
    progress_updated = pyqtSignal(int)
    data_updated = pyqtSignal(dict) 
    scraping_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_paused = False
        self.is_stopped = False
        self.product_count = 0
        self.max_products = 550  # You can adjust this limit
        self.csv_file_path = 'carsdata.csv'
        
        # Set up Selenium WebDriver
        service = Service(executable_path="C:/Users/Sher/Downloads/chromedriver-win64 (1)/chromedriver-win64/chromedriver.exe")
        options = webdriver.ChromeOptions()
        options.add_argument('--enable-gpu')
        options.add_argument('--svm-disable')
        options.page_load_strategy = 'eager' 
        # enable gpu, sandbox off,aur svm disable usage kiya tb huwa fast
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--no-sandbox')
        self.driver = webdriver.Chrome(service=service, options=options)

    def run(self):
        start_page =50
        for page_number in range(start_page, 1500):  # Adjust page limit as needed
            while self.is_paused:  # Check if paused
                time.sleep(0.1)  # Sleep briefly while paused

            if self.product_count >= self.max_products or self.is_stopped:
                break
        
            url = f"https://www.pakwheels.com/used-cars/family-cars/587667?page={page_number}"
            self.driver.get(url)

        # Use explicit wait to ensure the car cards are present
            try:
                WebDriverWait(self.driver, 3).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'search-title-row'))
            )
            except Exception as e:
                print(f"Error loading page: {e}")
                continue  
        
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')

        # Extract car data
            car_data_list = self.extract_car_data(soup)

        # Process each car's data
            for car_data in car_data_list:
                if self.product_count >= self.max_products or self.is_stopped:
                    break

            # Emit the car data
                self.data_updated.emit(car_data)  # Emit car data as a dictionary

            # Save the data to CSV
                self.save_to_csv(car_data)
                self.product_count += 1

            # Update the progress
                progress_value = (self.product_count * 100) // self.max_products
                self.progress_updated.emit(progress_value)

            # Sleep for a moment to avoid overwhelming the server
                # time.sleep(0.001)

        self.scraping_finished.emit()  # Emit finished signal
        self.driver.quit()  # Close the WebDriver

    def extract_car_data(self, soup):
        car_cards = soup.find_all('div', class_='search-title-row')  # Find all car cards
        car_data = []  # Initialize an empty list to store car data

        for card in car_cards:
            try:
                # Extract car name
                car_name_tag = card.find('a', class_='car-name')
                car_name = car_name_tag.get_text(strip=True) if car_name_tag else 'N/A'

                # Extract price
                price_tag = card.find('div', class_='price-details')
                price = price_tag.get_text(strip=True) if price_tag else 'N/A'

                # Extract sold by
                sold_by_tag = card.find('span', class_='sold-by-pw')
                sold_by = sold_by_tag.get_text(strip=True) if sold_by_tag else 'N/A'


                # Extract location and additional details
                details_card = card.find_next('div', class_='col-md-12 grid-date')
                location = 'N/A'
                model = mileage = fuel_type = engine_capacity = transmission = 'N/A'

                if details_card:
                    location_tag = details_card.find('li')
                    location = location_tag.get_text(strip=True) if location_tag else 'N/A'

                    details = details_card.find('ul', class_='list-unstyled search-vehicle-info-2 fs13')
                    if details:
                        detail_items = details.find_all('li')
                        if len(detail_items) > 0:
                            model = detail_items[0].get_text(strip=True)  # Model
                        if len(detail_items) > 1:
                            mileage = detail_items[1].get_text(strip=True)  # Mileage
                        if len(detail_items) > 2:
                            fuel_type = detail_items[2].get_text(strip=True)  # Fuel Type
                        if len(detail_items) > 3:
                            engine_capacity = detail_items[3].get_text(strip=True)  # Engine Capacity
                        if len(detail_items) > 4:
                            transmission = detail_items[4].get_text(strip=True)  # Transmission

                # Compile car information
                car_info = {
                    'Name': car_name,
                    'Price': price,
                    'Sold By': sold_by,
                    'Location': location,
                    'Model Year': model,
                    'Mileage': mileage,
                    'Fuel Type': fuel_type,
                    'Engine Capacity': engine_capacity,
                    'Transmission': transmission
                }
                car_data.append(car_info)  # Append car info to the list
                # print(f"Compiled Car Info: {car_info}")  # Print compiled car information

            except Exception as e:
                print(f"Error extracting car data: {e}")
                continue  # Skip if an element is missing

        return car_data  # Return the collected car data

    def save_to_csv(self, car_data):
        # Assuming 'car_data' is a dictionary with the relevant keys
        df = pd.DataFrame([car_data], columns=["Name", "Price", "Sold By", "Location", "Model Year", "Mileage", "Fuel Type", "Engine Capacity", "Transmission"])
        df.to_csv(self.csv_file_path, mode='a', header=not os.path.exists(self.csv_file_path), index=False)

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False
        

    def stop(self):
        self.is_stopped = True
        self.resume()
        self.driver.quit()

class MergedApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi()
        self.df = pd.DataFrame(columns=["Name", "Price", "Sold By", "Location", "Model Year", "Mileage", "Fuel Type", "Engine Capacity", "Transmission"])

        # Initialize the scraper thread
        self.scraper_thread = ScraperThread()
        self.scraper_thread.progress_updated.connect(self.update_progress)
        self.scraper_thread.data_updated.connect(self.update_table)
        self.scraper_thread.scraping_finished.connect(self.on_scraping_finished)
        
        # Connect scraper controls
        self.start_button.clicked.connect(self.start_scraping)
        self.pause_button.clicked.connect(self.pause_scraping)
        self.resume_button.clicked.connect(self.resume_scraping)
        self.stop_button.clicked.connect(self.stop_scraping)
        

    def setupUi(self):
        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("Web Scraper and Data Sorter")
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QGridLayout(self.central_widget)

    # Scraper controls layout
        self.scraper_controls = QHBoxLayout()  # Using QHBoxLayout for horizontal arrangement of buttons

    # Scraper controls
        self.start_button = self.create_button("Start Scraping", "#4CAF50", "#45a049")  # Green
        self.pause_button = self.create_button("Pause", "#FFA500", "#FF8C00")           # Orange
        self.resume_button = self.create_button("Resume", "#2196F3", "#1E88E5")         # Blue
        self.stop_button = self.create_button("Stop", "#F44336", "#D32F2F")            # Red

        self.scraper_controls.addWidget(self.start_button)
        self.scraper_controls.addWidget(self.pause_button)
        self.scraper_controls.addWidget(self.resume_button)
        self.scraper_controls.addWidget(self.stop_button)

    # Specify row and column for scraper controls layout
        self.layout.addLayout(self.scraper_controls, 0, 0, 1, 1)  # Add the layout with row and column

    # Table
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(9)
        self.tableWidget.setHorizontalHeaderLabels(["Name", "Price", "Sold By", "Location", "Model Year", "Mileage", "Fuel Type", "Engine Capacity", "Transmission"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.tableWidget, 1, 0, 1, 4)  # Table spans 4 columns

    # Progress bar
        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar, 2, 0, 1, 4)  # Place progress bar below the table

    # Sorting Time Label
        self.sorting_time_label = QLabel("Sorting Time: 0.0 seconds")
        self.layout.addWidget(self.sorting_time_label, 3, 0)

    # Load Button
        self.loadButton = self.create_button("Load Data", "#f44336", "#d32f2f")
        self.layout.addWidget(self.loadButton, 4, 0)

    # Sorting algorithm selection
        self.layout.addWidget(QLabel("Select a sorting algorithm:"), 5, 0)
        self.algorithmComboBox1 = self.create_combo_box(["Insertion Sort", "Selection Sort", "Bubble Sort", "Quick Sort", "Merge Sort", "Bucket Sort", "Radix Sort", "Counting Sort", "Shell Sort", "Pigeonhole Sort", "Comb Sort"])
        self.layout.addWidget(self.algorithmComboBox1, 5, 1)

    # Sorter controls
        self.layout.addWidget(QLabel("Sort by:"), 6, 0)
        self.columnComboBox1 = self.create_combo_box(["Name", "Price", "Location", "Model Year", "Mileage", "Fuel Type", "Engine Capacity", "Transmission"])
        self.layout.addWidget(self.columnComboBox1, 6, 1)

        self.layout.addWidget(QLabel("Then by:"), 7, 0)
        self.columnComboBox2 = self.create_combo_box(["None", "Name", "Price", "Location", "Model Year", "Mileage", "Fuel Type", "Engine Capacity", "Transmission"])
        self.layout.addWidget(self.columnComboBox2, 7, 1)

        self.sortButton = self.create_button("Sort", "#4CAF50", "#45a049")
        self.layout.addWidget(self.sortButton, 8, 0)

    # Search algorithm selection
        self.layout.addWidget(QLabel("Select a search algorithm:"), 9, 0)
        self.algorithmComboBox = self.create_combo_box(["Binary Search", "Linear Search"])
        self.layout.addWidget(self.algorithmComboBox, 9, 1)

    # Search controls
        self.layout.addWidget(QLabel("Search:"), 10, 0)
        self.searchLineEdit1 = self.create_line_edit("Search...")
        self.columnComboBoxSearch1 = self.create_combo_box(["Name", "Price", "Location", "Model Year", "Mileage", "Fuel Type", "Engine Capacity", "Transmission"])
        self.andOrNotComboBox1 = self.create_combo_box(["AND", "OR", "NOT"])
        self.layout.addWidget(self.searchLineEdit1, 10, 1)
        self.layout.addWidget(self.columnComboBoxSearch1, 10, 2)
        self.layout.addWidget(self.andOrNotComboBox1, 10, 3)

    # Second search level
        self.searchLineEdit2 = self.create_line_edit("Search...")
        self.columnComboBoxSearch2 = self.create_combo_box(["None", "Name", "Price", "Location", "Model Year", "Mileage", "Fuel Type", "Engine Capacity", "Transmission"])
        self.layout.addWidget(self.searchLineEdit2, 11, 1)
        self.layout.addWidget(self.columnComboBoxSearch2, 11, 2)

        self.searchButton = self.create_button("Search", "#f44336", "#d32f2f")
        self.resetButton = self.create_button("Reset", "#f44336", "#d32f2f")
        self.layout.addWidget(self.searchButton, 12, 0)
        self.layout.addWidget(self.resetButton, 12, 1)

    # Connect signals
        self.start_button.clicked.connect(self.start_scraping)
        self.sortButton.clicked.connect(self.sort_data)
        self.searchButton.clicked.connect(self.search_data)
        self.resetButton.clicked.connect(self.reset_data)
        self.loadButton.clicked.connect(self.load_data)

    def create_button(self, text, color, hover_color):
        button = QPushButton(text)
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color}; 
                color: white; 
                font-weight: bold; 
                border: none;
                padding: 10px;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
        """)
        return button

    def create_combo_box(self, items):
        combo_box = QComboBox()
        for item in items:
            combo_box.addItem(item)
        return combo_box

    def create_line_edit(self, placeholder):
        line_edit = QLineEdit()
        line_edit.setPlaceholderText(placeholder)
        return line_edit

    def load_data(self):
        self.df = pd.read_csv('check.csv')  # Change the file name as needed
        self.populate_table(self.df)

    def start_scraping(self):
        self.df = pd.DataFrame(columns=(["Name", "Price", "Sold By", "Location", "Model Year", "Mileage", "Fuel Type", "Engine Capacity", "Transmission"]))
        self.tableWidget.setRowCount(0)
        self.scraper_thread.is_stopped = False
        self.scraper_thread.start()

    def pause_scraping(self):
        self.scraper_thread.pause()

    def resume_scraping(self):
        self.scraper_thread.resume()

    def stop_scraping(self):
        self.scraper_thread.stop()
        self.scraper_thread.quit()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_table(self, product_data):
        row_position = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_position)

        for column_index, key in enumerate(product_data.keys()):
            self.tableWidget.setItem(row_position, column_index, QTableWidgetItem(str(product_data[key])))

        self.df = pd.concat([self.df, pd.DataFrame([product_data], columns=self.df.columns)], ignore_index=True)

    def update_table_from_df(self):
        # Clear the table
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(0)

        # Set the number of rows and columns based on the DataFrame
        num_rows, num_cols = self.df.shape
        self.tableWidget.setRowCount(num_rows)
        self.tableWidget.setColumnCount(num_cols)

        # Set the column headers
        self.tableWidget.setHorizontalHeaderLabels(self.df.columns)

        # Populate the table with the DataFrame values
        for i in range(num_rows):
            for j in range(num_cols):
                item = QTableWidgetItem(str(self.df.iat[i, j]))
                self.tableWidget.setItem(i, j, item)

        # Optionally adjust columns widths
        self.tableWidget.resizeColumnsToContents()

    def on_scraping_finished(self):
        print("Scraping finished!")

    def search_data(self):
        conditions = []
    
    # First search level
        search_text1 = self.searchLineEdit1.text().lower()
        selected_column1 = self.columnComboBoxSearch1.currentText()
    
        if search_text1 and selected_column1:
            conditions.append((selected_column1, search_text1))
    
    # Second search level
        search_text2 = self.searchLineEdit2.text().lower()
        selected_column2 = self.columnComboBoxSearch2.currentText()
    
        if search_text2 and selected_column2 != "None":
            conditions.append((selected_column2, search_text2))
    
    # Apply conditions based on AND/OR/NOT
        logic_operator = self.andOrNotComboBox1.currentText()
        filtered_df = self.df.copy()

        if logic_operator == "AND":
            for column, value in conditions:
                filtered_df = filtered_df[filtered_df[column].astype(str).str.contains(value, case=False)]
        elif logic_operator == "OR":
            temp_df = pd.DataFrame()
            for column, value in conditions:
                temp_df = pd.concat([temp_df, filtered_df[filtered_df[column].astype(str).str.contains(value, case=False)]])
            filtered_df = temp_df.drop_duplicates()
        elif logic_operator == "NOT":
            for column, value in conditions:
                filtered_df = filtered_df[~filtered_df[column].astype(str).str.contains(value, case=False)]
    
    # Now apply the selected search algorithm after filtering
        search_algorithm = self.algorithmComboBox1.currentText()
        #if search_algorithm is empty
        if not search_algorithm:
            return

        if search_algorithm == "Binary Search":
    # Apply binary search to the filtered dataframe
            for column, value in conditions:
                filtered_df = self.binary_search(filtered_df, column, value)
        elif search_algorithm == "Linear Search":
    # Apply linear search to the filtered dataframe
            for column, value in conditions:
                filtered_df = self.linear_search(filtered_df, column, value)
                if filtered_df.empty:
                    # If the search result is empty, display a message box
                    self.show_message_box("Search Result", "No results found!")
        else:
            pass

    
    # Populate the table with the final search result
        self.populate_table(filtered_df)

    # price convertor function
    def convert_price(self, price):
        if isinstance(price, str):
            # Price format is PKR 78.5lacs or PKR 1.8crore
            if "lac" in price:
                price = price.replace("PKR", "").replace("lacs", "").strip()
                price = float(price) * 100000
            elif "crore" in price:
                price = price.replace("PKR", "").replace("crore", "").strip()
                price = float(price) * 10000000 
        return price
    
    def sort_data(self):
        selected_columns = []

    # Get values from the first sorting level
        first_column = self.columnComboBox1.currentText()
        second_column = self.columnComboBox2.currentText()

        if first_column:
            selected_columns.append(first_column)
        
        if second_column != "None":
            selected_columns.append(second_column)

        if not selected_columns:
            return  # No columns selected for sorting

        start_time = time.time()
        selected_algorithm = self.algorithmComboBox1.currentText()
        # convert the data of Model Year column data to int
        # check if the selected column is Price
        
            
            
        
        # Sort the DataFrame first by the first column
        if selected_algorithm == "Insertion Sort":
            sorted_df = self.insertion_sort(self.df, first_column)
        elif selected_algorithm == "Selection Sort":
            sorted_df = self.selection_sort(self.df, first_column)
        elif selected_algorithm == "Bubble Sort":
            sorted_df = self.bubble_sort(self.df, first_column)
        elif selected_algorithm == "Quick Sort":
            sorted_df = self.quick_sort(self.df, first_column)
        elif selected_algorithm == "Merge Sort":
            sorted_df = self.merge_sort(self.df, first_column)
        elif selected_algorithm == "Bucket Sort":
            sorted_df = self.bucket_sort(self.df, first_column)
        elif selected_algorithm == "Radix Sort":
            sorted_df = self.radix_sort(self.df, first_column)
        elif selected_algorithm == "Counting Sort":
            sorted_df = self.counting_sort(self.df, first_column)
        elif selected_algorithm == "Shell Sort":
            sorted_df = self.shell_sort(self.df, first_column)
        elif selected_algorithm == "Pigeonhole Sort":
            sorted_df = self.pigeonhole_sort(self.df, first_column)
        elif selected_algorithm == "Comb Sort":
            sorted_df = self.comb_sort(self.df, first_column)
        else:
            sorted_df = self.df.copy()

    # Now sort by the second column if it is selected
        if second_column != "None":
            if selected_algorithm == "Insertion Sort":
                sorted_df = self.insertion_sort(sorted_df, second_column)
            elif selected_algorithm == "Selection Sort":
                sorted_df = self.selection_sort(sorted_df, second_column)
            elif selected_algorithm == "Bubble Sort":
                sorted_df = self.bubble_sort(sorted_df, second_column)
            elif selected_algorithm == "Quick Sort":
                sorted_df = self.quick_sort(sorted_df, second_column)
            elif selected_algorithm == "Merge Sort":
                sorted_df = self.merge_sort(sorted_df, second_column)
            elif selected_algorithm == "Bucket Sort":
                sorted_df = self.bucket_sort(sorted_df, second_column)
            elif selected_algorithm == "Radix Sort":
                sorted_df = self.radix_sort(sorted_df, second_column)
            elif selected_algorithm == "Counting Sort":
                sorted_df = self.counting_sort(sorted_df, second_column)
            elif selected_algorithm == "Shell Sort":
                sorted_df = self.shell_sort(sorted_df, second_column)
            elif selected_algorithm == "Pigeonhole Sort":
                sorted_df = self.pigeonhole_sort(sorted_df, second_column)
            elif selected_algorithm == "Comb Sort":
                sorted_df = self.comb_sort(sorted_df, second_column)

        end_time = time.time()
        sorting_time = end_time - start_time
        self.sorting_time_label.setText(f"Sorting Time: {sorting_time:.2f} seconds")
        
        self.df = sorted_df
        
        self.update_table_from_df()

        
    

      # Reset data
    def reset_data(self):
        self.populate_table(self.df)
        self.searchLineEdit1.clear()
        self.searchLineEdit2.clear()
        self.columnComboBox1.setCurrentIndex(0)
        self.columnComboBox2.setCurrentIndex(0)
        self.algorithmComboBox1.setCurrentIndex(0)
        self.sorting_time_label.setText("Sorting Time: 0.0 seconds")
        # Reset table data
        # self.df = pd.read_csv('check.csv')
        self.update_table_from_df()
        
    
    def populate_table(self, df):
        self.tableWidget.setRowCount(0)
        for index, row in df.iterrows():
            row_position = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row_position)
            for column_index, value in enumerate(row):
                self.tableWidget.setItem(row_position, column_index, QTableWidgetItem(str(value)))

    def insertion_sort(self, df, column):
        sorted_df = df.copy()  # Create a copy to avoid modifying the original DataFrame

        for i in range(1, len(sorted_df)):
            key = sorted_df.iloc[i]  # Get the current row as the key
            j = i - 1

            # Move elements that are greater than key[column] one position ahead
            while j >= 0 and sorted_df.iloc[j][column] > key[column]:
                sorted_df.iloc[j + 1] = sorted_df.iloc[j]  # Shift row j to j+1
                j -= 1

            sorted_df.iloc[j + 1] = key  # Insert the key row at its correct position

        return sorted_df

    def selection_sort(self, df, column):
        sorted_df = df.copy()  # Create a copy to avoid modifying the original DataFrame

        for i in range(len(sorted_df)):
            min_idx = i

            for j in range(i + 1, len(sorted_df)):
                # Compare elements regardless of their type
                if pd.isna(sorted_df[column].iloc[j]):
                    continue  # Skip NaN values
                if pd.isna(sorted_df[column].iloc[min_idx]) or sorted_df[column].iloc[j] < sorted_df[column].iloc[min_idx]:
                    min_idx = j

            # Swap the found minimum element with the first element
            sorted_df.iloc[i], sorted_df.iloc[min_idx] = sorted_df.iloc[min_idx].copy(), sorted_df.iloc[i].copy()

        return sorted_df
    
    def bubble_sort(self, df, column):
        sorted_df = df.copy()  # Create a copy to avoid modifying the original DataFrame
        n = len(sorted_df)

        for i in range(n):
            isSwapped = False
            for j in range(n - 1 - i):  # Reduce range as the largest elements bubble to the end
            # Ensure valid comparisons based on types
                if isinstance(sorted_df[column].iloc[j], str) and isinstance(sorted_df[column].iloc[j + 1], str):
                    if sorted_df[column].iloc[j] > sorted_df[column].iloc[j + 1]:
                        sorted_df.iloc[j], sorted_df.iloc[j + 1] = sorted_df.iloc[j + 1], sorted_df.iloc[j]
                        isSwapped = True
                elif isinstance(sorted_df[column].iloc[j], (int, float)) and isinstance(sorted_df[column].iloc[j + 1], (int, float)):
                    if sorted_df[column].iloc[j] > sorted_df[column].iloc[j + 1]:
                        sorted_df.iloc[j], sorted_df.iloc[j + 1] = sorted_df.iloc[j + 1], sorted_df.iloc[j]
                        isSwapped = True
                elif isinstance(sorted_df[column].iloc[j], str):
                # If j+1 is a number, keep j
                    continue  # Strings are treated as larger than numbers
                elif isinstance(sorted_df[column].iloc[j + 1], str):
                # If j is a number and j+1 is a string, swap j with j+1
                    sorted_df.iloc[j], sorted_df.iloc[j + 1] = sorted_df.iloc[j + 1], sorted_df.iloc[j]
                    isSwapped = True

            if not isSwapped:
                break  # No swaps mean the array is sorted

        return sorted_df

    def quick_sort(self, df, column):
        sorted_df = df.copy()
        if len(sorted_df) <= 1:
            return sorted_df
    
    # Choose pivot
        pivot = sorted_df[column].iloc[len(sorted_df) // 2]

    # Create left, middle, right DataFrames based on the pivot
        left = sorted_df[sorted_df[column] < pivot]
        middle = sorted_df[sorted_df[column] == pivot]
        right = sorted_df[sorted_df[column] > pivot]

        return pd.concat([self.quick_sort(left, column), middle, self.quick_sort(right, column)])

    def merge_sort(self, df, column):
        # Implement Merge Sort
        sorted_df = df.copy()
        if len(sorted_df) <= 1:
            return sorted_df
        mid = len(sorted_df) // 2
        left_half = self.merge_sort(sorted_df.iloc[:mid], column)
        right_half = self.merge_sort(sorted_df.iloc[mid:], column)
        return self.merge(left_half, right_half, column)

    def merge(self, left, right, column):
        result = pd.DataFrame(columns=left.columns)
        i = j = 0
        # Merge the two halves while there are elements in both
        while i < len(left) and j < len(right):
            if left[column].iloc[i] <= right[column].iloc[j]:
                result = pd.concat([result, left.iloc[[i]]],ignore_index=True)
                i += 1
            else:
                result = pd.concat([result, right.iloc[[j]]],ignore_index=True)
                j += 1
        
        # If there are remaining elements in the left half, add them
        while i < len(left):
            result = pd.concat([result, left.iloc[[i]]])
            i += 1
        
        # If there are remaining elements in the right half, add them
        while j < len(right):
            result = pd.concat([result, right.iloc[[j]]])
            j += 1
            
        return result

    def bucket_sort(self, df, column):
        # Implement Bucket Sort
        sorted_df = df.copy()
        max_value = sorted_df[column].max()
        min_value = sorted_df[column].min()
        bucket_range = (max_value - min_value) / len(sorted_df)

        buckets = [[] for _ in range(len(sorted_df))]
        for value in sorted_df[column]:
            index = int((value - min_value) / bucket_range)
            if index >= len(sorted_df):
                index = len(sorted_df) - 1
            buckets[index].append(value)

        sorted_df = pd.concat([pd.Series(sorted(bucket)) for bucket in buckets])
        return sorted_df

    def radix_sort(self, df, column):
        # Implement Radix Sort
        sorted_df = df.copy()
        max_num = sorted_df[column].max()
        exp = 1
        while max_num // exp > 0:
            sorted_df = self.counting_sort_radix(sorted_df, column, exp)
            exp *= 10
        return sorted_df

    def counting_sort_radix(self, df, column, exp):
        sorted_df = df.copy()
        output = [0] * len(sorted_df)
        count = [0] * 10

        for value in df[column]:
            index = value // exp
            count[index % 10] += 1

        for i in range(1, len(count)):
            count[i] += count[i - 1]

        for i in range(len(sorted_df) - 1, -1, -1):
            index = df[column].iloc[i] // exp
            output[count[index % 10] - 1] = df.iloc[i]
            count[index % 10] -= 1

        for i in range(len(sorted_df)):
            sorted_df.iloc[i] = output[i]
        return sorted_df

    def counting_sort(self, df, column):
        column_dtype = df[column].dtype

        if pd.api.types.is_numeric_dtype(column_dtype):
            sorted_df = df.copy()
            values = sorted_df[column].astype(int)
            max_val = values.max()
            min_val = values.min()
            range_val = max_val - min_val + 1

            # Create count array
            count = np.zeros(range_val, dtype=int)
            np.add.at(count, values - min_val, 1)

            # Create cumulative count
            count = np.cumsum(count)

            # Create output array
            output = np.zeros(len(df), dtype=int)
            for i in range(len(df) - 1, -1, -1):
                count_idx = values.iloc[i] - min_val
                output_idx = count[count_idx] - 1
                output[output_idx] = i
                count[count_idx] -= 1

            # Use the output array to reorder the DataFrame
            return sorted_df.iloc[output].reset_index(drop=True)

        elif pd.api.types.is_string_dtype(column_dtype):
            return df.sort_values(by=column).reset_index(drop=True)

        else:
            return df
         
    def shell_sort(self, df, column):
        sorted_df = df.copy()
        n = len(sorted_df)
        gap = n // 2  # Initialize gap size

        while gap > 0:
            for i in range(gap, n):
                temp = sorted_df.iloc[i]
                j = i
            
            # Shift earlier gap-sorted elements up until the correct location for temp is found
                while j >= gap and sorted_df[column].iloc[j - gap] > temp[column]:
                    sorted_df.iloc[j] = sorted_df.iloc[j - gap]
                    j -= gap
            
                sorted_df.iloc[j] = temp
            gap //= 2
        return sorted_df

    def pigeonhole_sort(self, df, column):
        sorted_df = df.copy()
        column_dtype = sorted_df[column].dtype

        if pd.api.types.is_numeric_dtype(column_dtype):
            # Numeric sorting
            min_value = sorted_df[column].min()
            max_value = sorted_df[column].max()
        
            # Handle floating-point numbers by scaling
            if np.issubdtype(column_dtype, np.floating):
                scale_factor = 10 ** (int(np.log10(max_value - min_value)) + 1)
                sorted_df[column] = (sorted_df[column] * scale_factor).astype(int)
                min_value = sorted_df[column].min()
                max_value = sorted_df[column].max()

            size = max_value - min_value + 1
            holes = [[] for _ in range(size)]

            # Place each row index in its corresponding pigeonhole
            for idx, value in enumerate(sorted_df[column]):
                holes[int(value) - min_value].append(idx)

            # Flatten the holes to get the sorted order of indices
            sorted_indices = [idx for hole in holes for idx in hole]

            # Use the sorted indices to reorder the DataFrame
            sorted_df = sorted_df.iloc[sorted_indices].reset_index(drop=True)

            # If we scaled floating-point numbers, rescale them back
            if np.issubdtype(column_dtype, np.floating):
                sorted_df[column] = sorted_df[column].astype(float) / scale_factor

        elif pd.api.types.is_string_dtype(column_dtype):
            # String sorting
            unique_values = sorted(sorted_df[column].unique())
            value_to_index = {val: idx for idx, val in enumerate(unique_values)}

            size = len(unique_values)
            holes = [[] for _ in range(size)]

            # Place each row index in its corresponding pigeonhole
            for idx, value in enumerate(sorted_df[column]):
                holes[value_to_index[value]].append(idx)

            # Flatten the holes to get the sorted order of indices
            sorted_indices = [idx for hole in holes for idx in hole]

            # Use the sorted indices to reorder the DataFrame
            sorted_df = sorted_df.iloc[sorted_indices].reset_index(drop=True)

        else:
            print(f"Unsupported data type: {column_dtype}")

        return sorted_df   
    
    def comb_sort(self, df, column):
        sorted_df = df.copy()
        n = len(sorted_df)
        gap = n
        shrink = 1.3  # Shrink factor
        sorted = False

        while not sorted:
        # Update the gap value for this iteration
            gap = int(gap / shrink)
            if gap < 1:
                gap = 1
            sorted = True

        # Compare elements that are 'gap' apart
            for i in range(n - gap):
                if sorted_df[column].iloc[i] > sorted_df[column].iloc[i + gap]:
                # Swap if the elements are out of order
                    sorted_df.iloc[i], sorted_df.iloc[i + gap] = sorted_df.iloc[i + gap], sorted_df.iloc[i]
                    sorted = False

        return sorted_df

        # Adding Searching Algos

    def binary_search(self, df, column, value):
            sorted_df=df.copy()
            start = 0
            end=len(sorted_df)-1
            mid=0
            while start<=end:
                mid=(start+end)//2
                if sorted_df[column].iloc[mid]==value:
                    return mid
                elif sorted_df[column].iloc[mid]<value:
                    start=mid+1
                else:
                    end=mid-1
            return -1

    def linear_search(self, df, column, value):
            sorted_df=df.copy()
            for i in range(len(sorted_df)):
                if sorted_df[column].iloc[i]==value:
                    return i
            return -1


def main():
    app = QApplication(sys.argv)
    window = MergedApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()