import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QLineEdit, QLabel, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor
import sqlite3
import datetime
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# Scopes for the Google Calendar API
SCOPES = ['https://www.googleapis.com/auth/calendar']

class Todolist(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("To-Do List App with Google Calendar")
        self.setGeometry(300, 300, 600, 500)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        layout = QVBoxLayout(self.central_widget)

        # Title label
        title_label = QLabel("To-Do List")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 28px; font-weight: bold;")
        layout.addWidget(title_label)

        # Task input
        task_layout = QHBoxLayout()
        self.task_input = QLineEdit()
        self.task_input.setPlaceholderText("Enter task")
        task_layout.addWidget(QLabel("Task:"))
        task_layout.addWidget(self.task_input)

        # Priority input
        self.priority_box = QComboBox()
        self.priority_box.addItems(["High", "Medium", "Low"])
        task_layout.addWidget(QLabel("Priority:"))
        task_layout.addWidget(self.priority_box)

        layout.addLayout(task_layout)

        # Event time input
        event_time_layout = QHBoxLayout()
        self.event_time_input = QLineEdit()
        self.event_time_input.setPlaceholderText("YYYY-MM-DD HH:MM")
        event_time_layout.addWidget(QLabel("Event Time:"))
        event_time_layout.addWidget(self.event_time_input)
        layout.addLayout(event_time_layout)

        # Button layout
        button_layout = QHBoxLayout()
        self.add_task_button = QPushButton("Add Task")
        self.add_task_button.clicked.connect(self.add_task)  # Add task and sync to Google Calendar
        button_layout.addWidget(self.add_task_button)

        self.mark_done_button = QPushButton("Mark Task as Done")
        self.mark_done_button.clicked.connect(self.mark_task_as_done)
        button_layout.addWidget(self.mark_done_button)

        self.delete_task_button = QPushButton("Delete Task")
        self.delete_task_button.clicked.connect(self.delete_task)
        button_layout.addWidget(self.delete_task_button)

        layout.addLayout(button_layout)

        # Task table
        self.task_table = QTableWidget(0, 5)  # Changed to 5 to accommodate status
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

        self.add_task_to_google_calendar(task, event_time)

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

                if self.dark_mode_toggle.isChecked():
                    self.task_table.item(row_position, 2).setForeground(QBrush(QColor("#FFFFFF")))  
                else:
                    self.task_table.item(row_position, 2).setForeground(QBrush(QColor("#000000"))) 
                    
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
            # Apply dark mode styles
            self.setStyleSheet("""
                QWidget {
                    background-color: #2e2e2e;
                    color: #f0f0f0;
                }
                QLineEdit, QComboBox, QTableWidget {
                    background-color: #3e3e3e;
                    color: #f0f0f0;
                    border: 1px solid #565656;
                    border-radius: 5px;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QTableWidget {
                    alternate-background-color: #4b4b4b;
                    gridline-color: #666666;
                }
                QHeaderView::section {
                    background-color: #454545;
                    font-weight: bold;
                    font-size: 14px;
                    border: 1px solid #666666;
                }
            """)
        else:
            # Apply light mode styles
            self.setStyleSheet("""
                QWidget {
                    background-color: #f9f9f9;
                    color: #000000;
                }
                QLineEdit, QComboBox, QTableWidget {
                    background-color: #ffffff;
                    color: #000000;
                    border: 1px solid #c9c9c9;
                    border-radius: 5px;
                }
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
                QTableWidget {
                    alternate-background-color: #f9f9f9;
                    gridline-color: #dcdcdc;
                }
                QHeaderView::section {
                    background-color: #f0f0f0;
                    font-weight: bold;
                    font-size: 14px;
                    border: 1px solid #dcdcdc;
                }
            """)

    def add_task_to_google_calendar(self, task, event_time):
        creds = None
        if os.path.exists('Your file path'):
            creds = Credentials.from_authorized_user_file('Your file path', SCOPES)
        else:
            QMessageBox.warning(self, "File Error", "Token file not found.")
            return

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'C:/Python/Todolist/client_secret_483712238000-lndurh15es91829o8hmp924daj9u0ov0.apps.googleusercontent.com.json', SCOPES)
                creds = flow.run_local_server(port=0)
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())

        service = build('calendar', 'v3', credentials=creds)

        start_time = datetime.datetime.strptime(event_time, "%Y-%m-%d %H:%M")
        end_time = start_time + datetime.timedelta(hours=1)  # Assume 1-hour duration
        event = {
            'summary': task,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': 'UTC',
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': 'UTC',
            },
        }

        try:
            event = service.events().insert(calendarId='primary', body=event).execute()
            print('Event created: %s' % (event.get('htmlLink')))
        except Exception as e:
            QMessageBox.warning(self, "Google Calendar Error", str(e))

def main():
    app = QApplication(sys.argv)
    window = Todolist()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
