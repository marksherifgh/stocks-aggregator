import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTableWidget, QTableWidgetItem, QWidget, \
    QMessageBox, QLineEdit, QPushButton, QHBoxLayout
from PyQt5.QtCore import Qt


class QueryApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Stocks Aggregator")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        self.layout = QVBoxLayout()

        # Horizontal layout for search input and button
        self.search_layout = QHBoxLayout()

        # Search input
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search by code or name")
        self.search_layout.addWidget(self.search_input)

        # Search button
        self.search_button = QPushButton("Search", self)
        self.search_button.setFixedSize(100, 30)  # Set a fixed size to make the button smaller
        self.search_button.clicked.connect(self.execute_query)
        self.search_layout.addWidget(self.search_button)

        self.layout.addLayout(self.search_layout)

        # Table widget to display results
        self.table_widget = QTableWidget(self)
        self.layout.addWidget(self.table_widget)

        # Central widget
        central_widget = QWidget()
        central_widget.setLayout(self.layout)
        self.setCentralWidget(central_widget)

        # Execute the fixed query on startup
        self.execute_query()

    def execute_query(self):
        # Get search term from input
        search_term = self.search_input.text()

        # SQL query to retrieve data
        query = """
        SELECT 
            name,
            code,
            SUM(CASE WHEN type = 'B' THEN trading_value ELSE 0 END) AS total_buy_value,
            SUM(CASE WHEN type = 'S' THEN trading_value ELSE 0 END) AS total_sell_value
        FROM 
            Trades
        WHERE
            DATE(date) BETWEEN DATE('now', '-1 month') AND DATE('now')
        """

        if search_term:
            query += f" AND (name LIKE '%{search_term}%' OR code LIKE '%{search_term}%')"

        query += " GROUP BY code;"

        # Sample SQLite database connection
        connection = sqlite3.connect("sqlite.db")
        cursor = connection.cursor()

        connection.commit()

        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            # Set up the table widget with the query results
            self.table_widget.setRowCount(len(rows))
            if rows:
                # Adjust the number of columns to include the percentages
                self.table_widget.setColumnCount(4)
                self.table_widget.setHorizontalHeaderLabels(
                    ["Name", "Code", "Buy Percentage (%)", "Sell Percentage (%)"])

                for row_index, row_data in enumerate(rows):
                    name, code, total_buy_value, total_sell_value = row_data

                    total = total_buy_value + total_sell_value
                    if total:
                        buy_percentage = round((total_buy_value / total) * 100, 2)
                        sell_percentage = round((total_sell_value / total) * 100, 2)
                    else:
                        buy_percentage = 0
                        sell_percentage = 0

                    # Populate the table with name, code, buy percentage, and sell percentage
                    self.table_widget.setItem(row_index, 0, QTableWidgetItem(name))
                    self.table_widget.setItem(row_index, 1, QTableWidgetItem(code))
                    self.table_widget.setItem(row_index, 2, QTableWidgetItem(str(buy_percentage)))
                    self.table_widget.setItem(row_index, 3, QTableWidgetItem(str(sell_percentage)))

                    # Center-align the text in the cells
                    for col in range(4):
                        self.table_widget.item(row_index, col).setTextAlignment(Qt.AlignCenter)

                # Adjust column widths to fit data
                self.table_widget.resizeColumnsToContents()
            else:
                self.table_widget.clearContents()
                self.table_widget.setRowCount(0)
                QMessageBox.information(self, "No Results", "The query returned no results.")
        except sqlite3.Error as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
        finally:
            connection.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QueryApp()
    window.show()
    sys.exit(app.exec_())
