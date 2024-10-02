import sys
import pandas as pd
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QTableWidgetItem

class Ui_DataSorter(object):
    def setupUi(self, DataSorter):
        DataSorter.setObjectName("DataSorter")
        DataSorter.resize(800, 600)

        self.centralwidget = QtWidgets.QWidget(DataSorter)
        self.centralwidget.setObjectName("centralwidget")

        self.searchLineEdit = QtWidgets.QLineEdit(self.centralwidget)
        self.searchLineEdit.setGeometry(QtCore.QRect(30, 30, 200, 30))
        self.searchLineEdit.setObjectName("searchLineEdit")

        self.searchButton = QtWidgets.QPushButton(self.centralwidget)
        self.searchButton.setGeometry(QtCore.QRect(250, 30, 100, 30))
        self.searchButton.setObjectName("searchButton")
        self.searchButton.setText("Search")

        self.resetButton = QtWidgets.QPushButton(self.centralwidget)
        self.resetButton.setGeometry(QtCore.QRect(600, 30, 100, 30))
        self.resetButton.setObjectName("resetButton")
        self.resetButton.setText("Reset")

        self.columnComboBox = QtWidgets.QComboBox(self.centralwidget)
        self.columnComboBox.setGeometry(QtCore.QRect(30, 80, 200, 30))
        self.columnComboBox.setObjectName("columnComboBox")

        self.algorithmComboBox = QtWidgets.QComboBox(self.centralwidget)
        self.algorithmComboBox.setGeometry(QtCore.QRect(250, 80, 200, 30))
        self.algorithmComboBox.setObjectName("algorithmComboBox")

        self.sortButton = QtWidgets.QPushButton(self.centralwidget)
        self.sortButton.setGeometry(QtCore.QRect(470, 80, 100, 30))
        self.sortButton.setObjectName("sortButton")
        self.sortButton.setText("Sort")

        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setGeometry(QtCore.QRect(30, 130, 740, 400))
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)

        DataSorter.setCentralWidget(self.centralwidget)

        self.menubar = QtWidgets.QMenuBar(DataSorter)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 25))
        self.menubar.setObjectName("menubar")
        DataSorter.setMenuBar(self.menubar)

        self.statusbar = QtWidgets.QStatusBar(DataSorter)
        self.statusbar.setObjectName("statusbar")
        DataSorter.setStatusBar(self.statusbar)

        self.retranslateUi(DataSorter)
        QtCore.QMetaObject.connectSlotsByName(DataSorter)

    def retranslateUi(self, DataSorter):
        _translate = QtCore.QCoreApplication.translate
        DataSorter.setWindowTitle(_translate("DataSorter", "Data Sorter"))

class DataSorterApp(QtWidgets.QMainWindow, Ui_DataSorter):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.load_data()

        self.searchButton.clicked.connect(self.search_data)
        self.sortButton.clicked.connect(self.sort_data)
        self.resetButton.clicked.connect(self.reset_data)


    def load_data(self):
        # Load data from CSV
        self.df = pd.read_csv('population_by_country_2020.csv')  # Update the path to your CSV file
        self.populate_table()

        # Set column headers in combo boxes
        headers = list(self.df.columns)
        self.columnComboBox.addItems(headers)
        self.algorithmComboBox.addItems([
            'Insertion Sort', 'Selection Sort', 'Bubble Sort', 
            'Quick Sort', 'Merge Sort', 'Bucket Sort', 
            'Radix Sort', 'Counting Sort'
        ])

    def populate_table(self):
        self.tableWidget.setRowCount(self.df.shape[0])
        self.tableWidget.setColumnCount(self.df.shape[1])
        self.tableWidget.setHorizontalHeaderLabels(list(self.df.columns))

        for row in range(self.df.shape[0]):
            for column in range(self.df.shape[1]):
                self.tableWidget.setItem(row, column, QTableWidgetItem(str(self.df.iat[row, column])))

    def search_data(self):
        search_text = self.searchLineEdit.text().lower()
        filtered_df = self.df[self.df.apply(lambda row: row.astype(str).str.contains(search_text).any(), axis=1)]
        self.df = filtered_df
        self.populate_table()

    def sort_data(self):
        selected_column = self.columnComboBox.currentText()
        selected_algorithm = self.algorithmComboBox.currentText()

        if selected_algorithm and selected_column:
            if selected_column in self.df.select_dtypes(include=['object']).columns:
                # String data sorting algorithms only
                self.df = self.df.sort_values(by=selected_column, kind='mergesort')  # Example with merge sort
            else:
                # Numeric data sorting algorithms
                if selected_algorithm == 'Insertion Sort':
                    self.df = self.insertion_sort(self.df, selected_column)
                elif selected_algorithm == 'Selection Sort':
                    self.df = self.selection_sort(self.df, selected_column)
                elif selected_algorithm == 'Bubble Sort':
                    self.df = self.bubble_sort(self.df, selected_column)
                elif selected_algorithm == 'Quick Sort':
                    self.df = self.quick_sort(self.df, selected_column)
                elif selected_algorithm == 'Merge Sort':
                    self.df = self.merge_sort(self.df, selected_column)
                elif selected_algorithm == 'Bucket Sort':
                    self.df = self.bucket_sort(self.df, selected_column)
                elif selected_algorithm == 'Radix Sort':
                    self.df = self.radix_sort(self.df, selected_column)
                elif selected_algorithm == 'Counting Sort':
                    self.df = self.counting_sort(self.df, selected_column)

            self.populate_table()

    def insertion_sort(self, df, column):
        sorted_df = df.copy()
        for i in range(1, len(sorted_df)):
            key = sorted_df[column].iloc[i]
            j = i - 1
            while j >= 0 and sorted_df[column].iloc[j] > key:
                j -= 1
            sorted_df.loc[i] = sorted_df.loc[j + 1]
        return sorted_df

    def reset_data(self):
        self.load_data()  # Reload the original data
        self.searchLineEdit.clear()  # Clear the search box
        self.columnComboBox.setCurrentIndex(0)  # Reset the column selection
        self.algorithmComboBox.setCurrentIndex(0)  # Reset the algorithm selection

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

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = DataSorterApp()
    window.show()
    sys.exit(app.exec_())


