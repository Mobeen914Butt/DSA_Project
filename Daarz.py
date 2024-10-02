import sys
import os
import pandas as pd
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QPushButton,
    QProgressBar, QTableWidget, QTableWidgetItem, QWidget,
    QHBoxLayout, QHeaderView
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

    def save_to_csv(self, product_data):
        df = pd.DataFrame([product_data], columns=["Product Name", "Price", "Sold", "Location", "Rating"])
        df.to_csv(self.csv_file_path, mode='a', header=not os.path.exists(self.csv_file_path), index=False)


    def pause(self):
        self.is_paused = True  # Set paused to True

    def resume(self):
        self.is_paused = False  # Set paused to False

    def stop(self):
        self.is_stopped = True  # Set stopped to True
        self.resume()  # Ensure thread can exit if paused
        self.driver.quit()  # Quit the driver


class ScraperApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Web Scraper")
        self.setGeometry(100, 100, 600, 400)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.progress_bar = QProgressBar(self)
        self.layout.addWidget(self.progress_bar)

        self.table = QTableWidget(self)
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Product Name", "Price", "Sold", "Location", "Rating"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.layout.addWidget(self.table)

        self.button_layout = QHBoxLayout()
        self.start_button = QPushButton("Start", self)
        self.pause_button = QPushButton("Pause", self)
        self.resume_button = QPushButton("Resume", self)
        self.stop_button = QPushButton("Stop", self)

        self.button_layout.addWidget(self.start_button)
        self.button_layout.addWidget(self.pause_button)
        self.button_layout.addWidget(self.resume_button)
        self.button_layout.addWidget(self.stop_button)

        self.layout.addLayout(self.button_layout)

        self.start_button.clicked.connect(self.start_scraping)
        self.pause_button.clicked.connect(self.pause_scraping)
        self.resume_button.clicked.connect(self.resume_scraping)
        self.stop_button.clicked.connect(self.stop_scraping)

        self.scraper_thread = ScraperThread()
        self.scraper_thread.progress_updated.connect(self.update_progress)
        self.scraper_thread.data_updated.connect(self.update_table)

        # Ensure the thread is stopped when the application closes
        self.destroyed.connect(self.stop_scraping)

    def start_scraping(self):
        self.scraper_thread.is_stopped = False
        self.scraper_thread.start()

    def pause_scraping(self):
        self.scraper_thread.pause()

    def resume_scraping(self):
        self.scraper_thread.resume()

    def stop_scraping(self):
        self.scraper_thread.stop()
        self.scraper_thread.quit()  # Quit the thread safely

   

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def update_table(self, product_data):
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        for i, data in enumerate(product_data):
            self.table.setItem(row_position, i, QTableWidgetItem(data))


def main():
    app = QApplication(sys.argv)
    window = ScraperApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
