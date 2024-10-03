import sys
import os
# print("Current working directory: ", os.getcwd())
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton,
    QProgressBar, QTableWidget, QTableWidgetItem, QWidget,
    QHBoxLayout, QHeaderView, QLineEdit, QComboBox, QLabel
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
        self.max_products = 25500  # You can adjust this limit
        self.csv_file_path = 'carsdata.csv'
        
        # Set up Selenium WebDriver
        service = Service(executable_path="D:\Semester 3\DSA\chromedriver-win64\chromedriver-win64\chromedriver.exe")
        options = webdriver.ChromeOptions()
        # # options.add_argument('--headless')  # Run the browser in the background
        # options.add_argument('--enable-gpu')
        options.page_load_strategy = 'eager' 
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        # # make code that takes less amount of internet
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-browser-side-navigation')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-offer-store-unmasked-wallet-cards')
        options.add_argument('--disable-offer-upload-credit-cards')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-print-preview')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-extensions') 


        # INcreasing load speed of web page
        # options.add_argument('--disable-gpu')
        # options.add_argument('--no-sandbox')
        # options.add_argument('--disable-dev-shm-usage')
        self.driver = webdriver.Chrome(service=service, options=options)

    def run(self):
        start_page = 250
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
                # time.sleep(0.1)

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
        self.df = pd.DataFrame( columns=["Name", "Price", "Sold By", "Location", "Model Year", "Mileage", "Fuel Type", "Engine Capacity", "Transmission"])

    def setupUi(self):
        self.setWindowTitle("Web Scraper and Data Sorter")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Scraper controls
        self.scraper_controls = QHBoxLayout()
        self.start_button = QPushButton("Start Scraping")
        self.pause_button = QPushButton("Pause")
        self.resume_button = QPushButton("Resume")
        self.stop_button = QPushButton("Stop")
        self.scraper_controls.addWidget(self.start_button)
        self.scraper_controls.addWidget(self.pause_button)
        self.scraper_controls.addWidget(self.resume_button)
        self.scraper_controls.addWidget(self.stop_button)
        self.layout.addLayout(self.scraper_controls)

        self.progress_bar = QProgressBar()
        self.layout.addWidget(self.progress_bar)

        # Sorter controls
        self.sorter_controls = QHBoxLayout()
        self.searchLineEdit = QLineEdit()
        self.searchLineEdit.setPlaceholderText("Search...")
        self.searchButton = QPushButton("Search")
        self.resetButton = QPushButton("Reset")
        self.columnComboBox = QComboBox()
        self.algorithmComboBox = QComboBox()
        self.sortButton = QPushButton("Sort")
        self.sorter_controls.addWidget(self.searchLineEdit)
        self.sorter_controls.addWidget(self.searchButton)
        self.sorter_controls.addWidget(self.resetButton)
        self.sorter_controls.addWidget(self.columnComboBox)
        self.sorter_controls.addWidget(self.algorithmComboBox)
        self.sorter_controls.addWidget(self.sortButton)
        self.layout.addLayout(self.sorter_controls)

        # Sorting Time Label
        self.sorting_time_label = QLabel("Sorting Time: 0.0 seconds")
        self.layout.addWidget(self.sorting_time_label)

        # Table
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(9) # add one more column for Discount
        self.tableWidget.setHorizontalHeaderLabels(["Name", "Price", "Sold By", "Location", "Model Year", "Mileage", "Fuel Type", "Engine Capacity", "Transmission"])
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.tableWidget)

        # Connect signals
        self.start_button.clicked.connect(self.start_scraping)
        self.pause_button.clicked.connect(self.pause_scraping)
        self.resume_button.clicked.connect(self.resume_scraping)
        self.stop_button.clicked.connect(self.stop_scraping)
        self.searchButton.clicked.connect(self.search_data)
        self.sortButton.clicked.connect(self.sort_data)
        self.resetButton.clicked.connect(self.reset_data)

        self.scraper_thread = ScraperThread()
        self.scraper_thread.progress_updated.connect(self.update_progress)
        self.scraper_thread.data_updated.connect(self.update_table)
        self.scraper_thread.scraping_finished.connect(self.on_scraping_finished)

        # Set column headers in combo boxes
        self.columnComboBox.addItems(["Name", "Price", "Sold By", "Location", "Model Year", "Mileage", "Fuel Type", "Engine Capacity", "Transmission"]) 
        self.algorithmComboBox.addItems([
            'Insertion Sort', 'Selection Sort', 'Bubble Sort', 
            'Quick Sort', 'Merge Sort', 'Bucket Sort', 
            'Radix Sort', 'Counting Sort', 'Shell Sort',
            'Pigeonhole Sort', 'Comb Sort'

        ])

        

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

    # def update_table(self, product_data):
    #     row_position = self.tableWidget.rowCount()
    #     self.tableWidget.insertRow(row_position)
    #     for i, data in enumerate(product_data):
    #         self.tableWidget.setItem(row_position, i, QTableWidgetItem(str(data)))
        
    #     # Update the DataFrame
    #     self.df = pd.concat([self.df, pd.DataFrame([product_data], columns=self.df.columns)], ignore_index=True)
    def update_table(self, product_data):
        row_position = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row_position)
    
        for column_index, key in enumerate(product_data.keys()):
            self.tableWidget.setItem(row_position, column_index, QTableWidgetItem(str(product_data[key])))

        self.df = pd.concat([self.df, pd.DataFrame([product_data], columns=self.df.columns)], ignore_index=True)

    def on_scraping_finished(self):
        print("Scraping finished!")
        # You can add any additional actions here, like enabling/disabling buttons

    def search_data(self):
        search_text = self.searchLineEdit.text().lower()
        filtered_df = self.df[self.df.apply(lambda row: row.astype(str).str.contains(search_text).any(), axis=1)]
        self.populate_table(filtered_df)

    def sort_data(self):
        selected_column = self.columnComboBox.currentText()
        selected_algorithm = self.algorithmComboBox.currentText()

        if selected_algorithm and selected_column:
            start_time = time.time()
            if selected_algorithm == 'Insertion Sort':
                sorted_df = self.insertion_sort(self.df, selected_column)
            elif selected_algorithm == 'Selection Sort':
                sorted_df = self.selection_sort(self.df, selected_column)
            elif selected_algorithm == 'Bubble Sort':
                sorted_df = self.bubble_sort(self.df, selected_column)
            elif selected_algorithm == 'Quick Sort':
                sorted_df = self.quick_sort(self.df, selected_column)
            elif selected_algorithm == 'Merge Sort':
                sorted_df = self.merge_sort(self.df, selected_column)
            elif selected_algorithm == 'Bucket Sort':
                sorted_df = self.bucket_sort(self.df, selected_column)
            elif selected_algorithm == 'Radix Sort':
                sorted_df = self.radix_sort(self.df, selected_column)
            elif selected_algorithm == 'Counting Sort':
                sorted_df = self.counting_sort(self.df, selected_column)
            elif selected_algorithm == 'Shell Sort':
                sorted_df = self.shell_sort(self.df, selected_column)
            elif selected_algorithm == 'Pigeonhole Sort':
                sorted_df = self.pigeonhole_sort(self.df, selected_column)
            elif selected_algorithm == 'Comb Sort':
                sorted_df = self.comb_sort(self.df, selected_column)

            

            end_time = time.time()
            sorting_time = end_time - start_time
            self.sorting_time_label.setText(f"Sorting Time: {sorting_time:.2f} seconds")
            self.populate_table(sorted_df)

    def reset_data(self):
        self.populate_table(self.df)
        self.searchLineEdit.clear()
        self.columnComboBox.setCurrentIndex(0)
        self.algorithmComboBox.setCurrentIndex(0)

    def populate_table(self, df):
        self.tableWidget.setRowCount(df.shape[0])
        self.tableWidget.setColumnCount(df.shape[1])
        self.tableWidget.setHorizontalHeaderLabels(list(df.columns))

        for row in range(df.shape[0]):
            for column in range(df.shape[1]):
                self.tableWidget.setItem(row, column, QTableWidgetItem(str(df.iat[row, column])))

    # Sorting algorithms (insertion_sort, selection_sort, etc.) remain the same

    # def insertion_sort(self, df, column):
    #     sorted_df = df.copy()
    #     for i in range(1, len(sorted_df)):
    #         key = sorted_df.iloc[i]
    #         j = i - 1
    #         while j >= 0 and key[column] < sorted_df.iloc[j][column]:
    #             sorted_df.iloc[j + 1] = sorted_df.iloc[j]
    #             j -= 1
    #         sorted_df.iloc[j + 1] = key
    #     return sorted_df
def insertion_sort(self, df, column):
    sorted_df = df.copy()  # Create a copy to avoid modifying the original DataFrame
    for i in range(1, len(sorted_df)):
        key = sorted_df.iloc[i]
        j = i - 1

        # Compare key with the previous elements
        while j >= 0:
            # Ensure comparison is valid (both should be of the same type)
            if isinstance(key[column], str) and isinstance(sorted_df.iloc[j][column], str):
                if key[column] < sorted_df.iloc[j][column]:
                    sorted_df.iloc[j + 1] = sorted_df.iloc[j]
                else:
                    break  # Stop if the order is correct
            elif isinstance(key[column], (int, float)) and isinstance(sorted_df.iloc[j][column], (int, float)):
                if key[column] < sorted_df.iloc[j][column]:
                    sorted_df.iloc[j + 1] = sorted_df.iloc[j]
                else:
                    break  # Stop if the order is correct
            else:
                # If types are mixed, we can define a strategy (e.g., place strings after numbers)
                if isinstance(key[column], str):
                    break  # Stop since we consider strings after numbers
            j -= 1

        sorted_df.iloc[j + 1] = key  # Place the key in the correct position
    return sorted_df



    # def selection_sort(self, df, column):
    #     sorted_df = df.copy()
    #     for i in range(len(sorted_df)):
    #         min_idx = i
    #         for j in range(i + 1, len(sorted_df)):
    #             if sorted_df[column].iloc[j] < sorted_df[column].iloc[min_idx]:
    #                 min_idx = j
    #         sorted_df.iloc[i], sorted_df.iloc[min_idx] = sorted_df.iloc[min_idx], sorted_df.iloc[i]
    #     return sorted_df
def selection_sort(self, df, column):
    sorted_df = df.copy()  # Create a copy to avoid modifying the original DataFrame
    for i in range(len(sorted_df)):
        min_idx = i
        for j in range(i + 1, len(sorted_df)):
            # Ensure valid comparisons based on types
            if isinstance(sorted_df[column].iloc[j], str) and isinstance(sorted_df[column].iloc[min_idx], str):
                if sorted_df[column].iloc[j] < sorted_df[column].iloc[min_idx]:
                    min_idx = j
            elif isinstance(sorted_df[column].iloc[j], (int, float)) and isinstance(sorted_df[column].iloc[min_idx], (int, float)):
                if sorted_df[column].iloc[j] < sorted_df[column].iloc[min_idx]:
                    min_idx = j
            elif isinstance(sorted_df[column].iloc[j], str):
                # If min_idx is a number, and j is a string, keep min_idx
                continue  # Strings are treated as larger than numbers
            elif isinstance(sorted_df[column].iloc[min_idx], str):
                min_idx = j  # If the current min_idx is a string, replace it with a number if found

        # Swap the found minimum element with the first element
        sorted_df.iloc[i], sorted_df.iloc[min_idx] = sorted_df.iloc[min_idx], sorted_df.iloc[i]

    return sorted_df

    # def bubble_sort(self, df, column):
    #     sorted_df = df.copy()
    #     n = len(sorted_df)
    #     for i in range(n):
    #         isSwapped = False
    #         for j in range(0, n-i-1):
    #             if sorted_df[column].iloc[j] > sorted_df[column].iloc[j + 1]:
    #                 sorted_df.iloc[j], sorted_df.iloc[j + 1] = sorted_df.iloc[j + 1], sorted_df.iloc[j]
    #                 isSwapped = True
    #         if not isSwapped:
    #             break
    #     return sorted_df

    # def bubble_sort(self, df, column):
    #     sorted_df = df.copy()
    #     n = len(sorted_df)
    #     for i in range(1,n):
    #         isSwapped = False
    #         for j in range(0,n-i):
    #             if sorted_df[column].iloc[j] > sorted_df[column].iloc[j+1]:
    #                 sorted_df.iloc[j], sorted_df.iloc[j+1] = sorted_df.iloc[j+1], sorted_df.iloc[j]
    #                 isSwapped = True
    #         if not isSwapped:
    #             break
    #     return sorted_df
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

    # def quick_sort(self, df, column):
    #     # Implement Quick Sort
    #     sorted_df = df.copy()
    #     if len(sorted_df) <= 1:
    #         return sorted_df
    #     pivot = sorted_df[column].iloc[len(sorted_df) // 2]
    #     left = sorted_df[sorted_df[column] < pivot]
    #     middle = sorted_df[sorted_df[column] == pivot]
    #     right = sorted_df[sorted_df[column] > pivot]
    #     return pd.concat([self.quick_sort(left, column), middle, self.quick_sort(right, column)])
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
        result = pd.DatasFrame(columns=left.columns)
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

    # def counting_sort(self, df, column):
    #     # Implement Counting Sort
    #     sorted_df = df.copy()
    #     max_val = sorted_df[column].max()
    #     count = [0] * (max_val + 1)

    #     for value in sorted_df[column]:
    #         count[value] += 1

    #     index = 0
    #     for i in range(max_val + 1):
    #         while count[i] > 0:
    #             sorted_df.iloc[index] = i
    #             index += 1
    #             count[i] -= 1
    #     return sorted_df

    def counting_sort(self, df, column):
        column_dtype = df[column].dtype

        if pd.api.types.is_numeric_dtype(column_dtype):
            sorted_df = df.copy()
            max_val = sorted_df[column].max()
            count = [0] * (max_val + 1)
            for value in sorted_df[column]:
                count[value] += 1

            index = 0
            for i in range(max_val + 1):
                while count[i] > 0:
                    sorted_df.iloc[index] = i
                    index += 1
                    count[i] -= 1
            return sorted_df

        elif pd.api.types.is_string_dtype(column_dtype):
            sorted_df=df.copy()
            sorted_df=sorted_df.sort_values(by=column).reset_index(drop=True)
            return sorted_df

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
    
    # Step 1: Find the range of the values
    min_value = sorted_df[column].min()
    max_value = sorted_df[column].max()
    
    # Step 2: Create pigeonholes
    size = max_value - min_value + 1
    holes = [[] for _ in range(size)]

    # Step 3: Place each element in its corresponding pigeonhole
    for value in sorted_df[column]:
        holes[value - min_value].append(value)

    # Step 4: Flatten the holes into the sorted order
    sorted_index = 0
    for hole in holes:
        for value in hole:
            sorted_df.iloc[sorted_index] = value
            sorted_index += 1
    
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



def main():
    app = QApplication(sys.argv)
    window = MergedApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()