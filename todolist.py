import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QLineEdit, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
import sqlite3
import os
import pytz
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/tasks']


class Todolist(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("To-Do List App with Google Calendar")
        self.setGeometry(300, 300, 600, 500)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout(self.central_widget)

        title_label = QLabel("To-Do List")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title_label)

        task_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter task")
        task_layout.addWidget(QLabel("Task:"))
        task_layout.addWidget(self.task_input)

        self.priority_box = QComboBox()
        self.priority_box.addItems(["High", "Medium", "Low"])
        task_layout.addWidget(QLabel("Priority:"))
        task_layout.addWidget(self.priority_box)
        layout.addLayout(task_layout)

        event_time_layout = QHBoxLayout()
        self.event_time_input = QLineEdit()
        self.event_time_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        event_time_layout.addWidget(QLabel("Event Time:"))
        event_time_layout.addWidget(self.event_time_input)
        layout.addLayout(event_time_layout)

        button_layout = QHBoxLayout()
        self.add_task_button = QPushButton("Add Task")
        self.add_task_button.clicked.connect(self.add_task)
        button_layout.addWidget(self.add_task_button)

        self.mark_done_button = QPushButton("Mark Task as Done")
        self.mark_done_button.clicked.connect(self.mark_task_as_done)
        button_layout.addWidget(self.mark_done_button)

        self.delete_task_button = QPushButton("Delete Task")
        self.delete_task_button.clicked.connect(self.delete_task)
        button_layout.addWidget(self.delete_task_button)
        layout.addLayout(button_layout)

        self.task_table = QTableWidget(0, 5)
        self.task_table.setHorizontalHeaderLabels(["ID", "Task", "Priority", "Event Time", "Status"])
        self.task_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.task_table)

        self.dark_mode_toggle = QCheckBox("Dark Mode")
        self.dark_mode_toggle.stateChanged.connect(self.toggle_dark_mode)
        layout.addWidget(self.dark_mode_toggle)

        self.conn = sqlite3.connect("todolist.db")
        self.create_table()

        self.priority_colors = {
            "High": "#FF9999",
            "Medium": "#FFFF99",
            "Low": "#99FF99"
        }

        self.load_tasks()

    def create_table(self):
        cursor = self.conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS tasks
                          (id INTEGER PRIMARY KEY, task TEXT, priority TEXT, event_time TEXT, done INTEGER)''')
        self.conn.commit()

    def add_task(self):
        task = self.task_input.text()
        priority = self.priority_box.currentText()
        event_time = self.event_time_input.text()

        if not task or not event_time:
            QMessageBox.warning(self, "Input Error", "Please fill in all fields.")
            return

        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO tasks (task, priority, event_time, done) VALUES (?, ?, ?, 0)",
                       (task, priority, event_time))
        self.conn.commit()
        self.load_tasks()

        self.add_task_to_google_tasks(task, event_time)

    def load_tasks(self):
        self.task_table.setRowCount(0)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks")
        tasks = cursor.fetchall()

        for task in tasks:
            row_position = self.task_table.rowCount()
            self.task_table.insertRow(row_position)
            for i, item in enumerate(task):
                self.task_table.setItem(row_position, i, QTableWidgetItem(str(item)))
            
            priority = task[2]
            if priority in self.priority_colors:
                color = self.priority_colors[priority]
                self.task_table.item(row_position, 2).setBackground(QBrush(QColor(color)))

            done = task[4]
            status_text = "Done" if done else "Pending"
            self.task_table.setItem(row_position, 4, QTableWidgetItem(status_text))

            # Adjust row color based on mode
            if self.dark_mode_toggle.isChecked():
                if done:
                    self.task_table.item(row_position, 4).setBackground(QBrush(QColor('#00FF00')))  # Green for done tasks
                else:
                    self.task_table.item(row_position, 4).setBackground(QBrush(QColor('#FF0000')))  # Red for pending tasks
            else:
                if done:
                    self.task_table.item(row_position, 4).setBackground(QBrush(QColor('#d4edda')))  # Light green for done
                else:
                    self.task_table.item(row_position, 4).setBackground(QBrush(QColor('#f8d7da')))  # Light red for pending

    def mark_task_as_done(self):
        selected_row = self.task_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Selection Error", "Please select a task to mark as done.")
            return

        task_id = int(self.task_table.item(selected_row, 0).text())
        cursor = self.conn.cursor()
        cursor.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,))
        self.conn.commit()
        self.load_tasks()

    def delete_task(self):
        selected_row = self.task_table.currentRow()
        if selected_row == -1:
            QMessageBox.warning(self, "Selection Error", "Please select a task to delete.")
            return

        task_id = int(self.task_table.item(selected_row, 0).text())
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
        self.load_tasks()

    def toggle_dark_mode(self):
        if self.dark_mode_toggle.isChecked():
            self.setStyleSheet("""
                QWidget { background-color: #2e2e2e; color: #f0f0f0; }
                QPushButton { background-color: #4CAF50; color: white; border-radius: 5px; }
                QPushButton:hover { background-color: #45a049; }
                QTableWidget { background-color: #3e3e3e; border: none; color: #f0f0f0; }
                QTableWidget::item { border-bottom: 1px solid #555; padding: 10px; }
                QTableWidget::item:selected { background-color: #5e5e5e; }
                QTableWidget::horizontalHeader { background-color: #2e2e2e; color: white; }
                QTableWidget::verticalHeader { background-color: #2e2e2e; color: white; }
                QCheckBox { color: white; }
            """)
        else:
            # White mode (Light mode) is now the default, so this will be used as the fallback style
            self.setStyleSheet("""
                QWidget { background-color: #f9f9f9; color: #000000; }
                QPushButton { background-color: #007BFF; color: white; border-radius: 5px; }
                QPushButton:hover { background-color: #0056b3; }
                QTableWidget { background-color: #ffffff; border: none; color: #000000; }
                QTableWidget::item { border-bottom: 1px solid #ddd; padding: 10px; }
                QTableWidget::item:selected { background-color: #cce5ff; }
                QTableWidget::horizontalHeader { background-color: #f0f0f0; color: black; }
                QTableWidget::verticalHeader { background-color: #f0f0f0; color: black; }
                QCheckBox { color: black; }
            """)

    def add_task_to_google_tasks(self, task, event_time):
        creds = None
        # Replace with your file path
        credential_path = 'credentials.json'
        token_path = 'token.json'

        # Load the credentials
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(credential_path, SCOPES)
                creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as token:
                token.write(creds.to_json())

        service = build('tasks', 'v1', credentials=creds)

        try:
            task_details = {
                'title': task,
                'due': event_time
            }
            service.tasks().insert(tasklist='@default', body=task_details).execute()
        except Exception as e:
            print(f"An error occurred: {e}")
            QMessageBox.warning(self, "Google Tasks Error", "Failed to add task to Google Tasks.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Todolist()
    window.show()
    sys.exit(app.exec_())
