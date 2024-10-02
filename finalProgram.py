import sys
import os
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton,
    QProgressBar, QTableWidget, QTableWidgetItem, QWidget,
    QHBoxLayout, QHeaderView, QLineEdit, QComboBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup

class ScraperThread(QThread):
    progress_updated = pyqtSignal(int)
    data_updated = pyqtSignal(list)
    scraping_finished = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.is_paused = False
        self.is_stopped = False
        self.product_count = 0
        self.max_products = 100  # You can adjust this limit
        self.csv_file_path = 'scraped_data.csv'
        
        # Set up Selenium WebDriver
        service = Service(executable_path="C:/Users/Sher/Downloads/chromedriver-win64 (1)/chromedriver-win64/chromedriver.exe")
        options = webdriver.ChromeOptions()
        self.driver = webdriver.Chrome(service=service, options=options)

    def run(self):
        queries = ['nails', 'nail polish']
        for query in queries:
            for page in range(1, 10):  # Adjust page limit as needed
                if self.product_count >= self.max_products or self.is_stopped:
                    break

                self.driver.get(f"https://www.daraz.pk/catalog/?q={query}&page={page}")

                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'buTCk'))
                    )
                except Exception as e:
                    print(f"Error loading products: {e}")
                    break

                content = self.driver.page_source
                soup = BeautifulSoup(content, "html.parser")
                mobiles = soup.find_all('div', attrs={'class': 'buTCk'})

                for mobile in mobiles:
                    if self.product_count >= self.max_products or self.is_stopped:
                        break

                    while self.is_paused:  # Check if paused
                        time.sleep(0.1)

                    try:
                        price = mobile.find('span', attrs={'class': 'ooOxS'}).text.strip()
                        name = mobile.find('div', attrs={'class': 'RfADt'}).find('a').text.strip()
                        sold = mobile.find('div', attrs={'class': '_6uN7R'}).find('span').text.strip()
                        location = mobile.find('span', attrs={'class': 'oa6ri'}).text.strip()
                        rate = mobile.find('span', attrs={'class': 'qzqFw'})
                        rate = rate.text.strip().strip('()') if rate else 'N/A'

                        product_data = [name, price, sold, location, rate]
                        self.data_updated.emit(product_data)
                        self.save_to_csv(product_data)

                        self.product_count += 1
                        progress_value = (self.product_count * 100) // self.max_products
                        self.progress_updated.emit(progress_value)

                        time.sleep(0.1)

                    except Exception as e:
                        print(f"Error scraping data: {e}")

        self.scraping_finished.emit()

    def save_to_csv(self, product_data):
        df = pd.DataFrame([product_data], columns=["Product Name", "Price", "Sold", "Location", "Rating"])
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
        self.df = pd.DataFrame(columns=["Product Name", "Price", "Sold", "Location", "Rating"])

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

        # Table
        self.tableWidget = QTableWidget()
        self.tableWidget.setColumnCount(5)
        self.tableWidget.setHorizontalHeaderLabels(["Product Name", "Price", "Sold", "Location", "Rating"])
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
        self.columnComboBox.addItems(["Product Name", "Price", "Sold", "Location", "Rating"])
        self.algorithmComboBox.addItems([
            'Insertion Sort', 'Selection Sort', 'Bubble Sort', 
            'Quick Sort', 'Merge Sort', 'Bucket Sort', 
            'Radix Sort', 'Counting Sort'
        ])

    def start_scraping(self):
        self.df = pd.DataFrame(columns=["Product Name", "Price", "Sold", "Location", "Rating"])
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
        for i, data in enumerate(product_data):
            self.tableWidget.setItem(row_position, i, QTableWidgetItem(str(data)))
        
        # Update the DataFrame
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

    def insertion_sort(self, df, column):
        sorted_df = df.copy()
        for i in range(1, len(sorted_df)):
            key = sorted_df[column].iloc[i]
            j = i - 1
            while j >= 0 and sorted_df[column].iloc[j] > key:
                j -= 1
            sorted_df.loc[i] = sorted_df.loc[j + 1]
        return sorted_df

    def selection_sort(self, df, column):
        sorted_df = df.copy()
        for i in range(len(sorted_df)):
            min_idx = i
            for j in range(i + 1, len(sorted_df)):
                if sorted_df[column].iloc[j] < sorted_df[column].iloc[min_idx]:
                    min_idx = j
            sorted_df.iloc[i], sorted_df.iloc[min_idx] = sorted_df.iloc[min_idx], sorted_df.iloc[i]
        return sorted_df

    def bubble_sort(self, df, column):
        sorted_df = df.copy()
        n = len(sorted_df)
        for i in range(n):
            for j in range(0, n-i-1):
                if sorted_df[column].iloc[j] > sorted_df[column].iloc[j + 1]:
                    sorted_df.iloc[j], sorted_df.iloc[j + 1] = sorted_df.iloc[j + 1], sorted_df.iloc[j]
        return sorted_df

    def quick_sort(self, df, column):
        # Implement Quick Sort
        sorted_df = df.copy()
        if len(sorted_df) <= 1:
            return sorted_df
        pivot = sorted_df[column].iloc[len(sorted_df) // 2]
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
                result = pd.concat([result, left.iloc[[i]]])
                i += 1
            else:
                result = pd.concat([result, right.iloc[[j]]])
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
        # Implement Counting Sort
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


def main():
    app = QApplication(sys.argv)
    window = MergedApp()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()