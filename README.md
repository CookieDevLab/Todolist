# 📝 To-Do List with Google Tasks Integration

A desktop-based To-Do List application built using **PyQt5** that helps you manage tasks locally and sync them with **Google Tasks**. It features priority tagging, event time scheduling, dark mode, and seamless integration with the Google Tasks API.

## 🚀 Features

- Add, delete, and mark tasks as done ✅
- Assign **priority levels** (High, Medium, Low) with colored indicators 🔴🟡🟢
- Schedule tasks using a date-time input 📅
- Enable **Dark Mode** for a comfortable viewing experience 🌙
- Sync tasks with **Google Tasks** using OAuth2 📤
- Local task storage using **SQLite** for offline access 💾

## 📸 Screenshots

### Light Mode
![Light Mode](screenshots/light_mode.png)

### Dark Mode
![Dark Mode](screenshots/dark_mode.png)

## 🛠️ Installation

### Prerequisites
- Python 3.7+
- A Google Cloud project with Google Tasks API enabled
- Your own `credentials.json` file for OAuth2

### Clone the repo
```bash
git clone https://github.com/<your-username>/todolist-google-tasks.git
cd todolist-google-tasks

## 🛠️ Installation

### Install dependencies
```bash
pip install -r requirements.txt

### Run the App
```bash 
python main.py

