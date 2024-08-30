import sys
import sqlite3
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QTableWidget, QTableWidgetItem, QWidget, QMessageBox


class QueryApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SQL Query App")
        self.setGeometry(100, 100, 800, 600)

        # Main layout
        self.layout = QVBoxLayout()

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
        # Fixed SQL query
        query = """SELECT 
    name,
    code,
    SUM(CASE WHEN type = 'B' THEN trading_value ELSE 0 END) AS total_buy_value,
    SUM(CASE WHEN type = 'S' THEN trading_value ELSE 0 END) AS total_sell_value
FROM 
    Trades
WHERE
    DATE(date) BETWEEN DATE('now', '-1 month') AND DATE('now')
GROUP BY 
    code;"""

        # Sample SQLite database connection
        connection = sqlite3.connect("sqlite.db")  # In-memory database, replace with your database
        cursor = connection.cursor()

        connection.commit()

        try:
            cursor.execute(query)
            rows = cursor.fetchall()

            # Set up the table widget with the query results
            self.table_widget.setRowCount(len(rows))
            if rows:
                self.table_widget.setColumnCount(len(rows[0]))
                self.table_widget.setHorizontalHeaderLabels([description[0] for description in cursor.description])

                for row_index, row_data in enumerate(rows):
                    for column_index, data in enumerate(row_data):
                        self.table_widget.setItem(row_index, column_index, QTableWidgetItem(str(data)))
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
