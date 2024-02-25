import sys
import threading
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QTextEdit, QFileDialog, QProgressBar, QLabel, QLineEdit
from PySide6.QtCore import Qt
from scraper import Scraper
from concurrent.futures import ThreadPoolExecutor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OnlyFans Username Scraper")
        self.setGeometry(100, 100, 800, 600)
        self.setStyleSheet(
            "QMainWindow {background-color: #333333; color: #ffffff;}"
            "QPushButton {background-color: #4A90E2; color: #ffffff; border-radius: 10px;}"
            "QPushButton:hover {background-color: #357EC7;}"
            "QTextEdit {background-color: #444444; color: #ffffff; border-radius: 5px;}"
            "QProgressBar {background-color: #666666; color: #ffffff; border-radius: 5px;}"
            "QLabel {color: #ffffff;}"
            "QLineEdit {background-color: #444444; color: #ffffff; border-radius: 5px;}"
        )

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.url_label = QLabel("Enter URLs (separated by commas):")
        self.url_input = QLineEdit()

        self.sign_in_button = QPushButton("Sign In to OnlyFans")
        self.sign_in_button.setStyleSheet("background-color: #FF7F0F; color: #ffffff; border-radius: 10px;")
        self.sign_in_button.setMaximumHeight(40)
        self.sign_in_button.clicked.connect(self.sign_in_onlyfans)

        self.button_layout = QVBoxLayout()
        self.scrape_button = QPushButton("Scrape Usernames")
        self.save_button = QPushButton("Save Usernames")
        self.clear_button = QPushButton("Clear Output")
        self.download_all_button = QPushButton("Download All Subscribed Users")
        self.scrape_button.setMaximumHeight(40)
        self.save_button.setMaximumHeight(40)
        self.clear_button.setMaximumHeight(40)
        self.download_all_button.setMaximumHeight(40)
        self.button_layout.addWidget(self.scrape_button)
        self.button_layout.addWidget(self.save_button)
        self.button_layout.addWidget(self.clear_button)
        self.button_layout.addWidget(self.download_all_button)

        self.output_label = QLabel("Output:")
        self.output_text = QTextEdit()

        self.progress_label = QLabel("Progress:")
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMinimumHeight(30)

        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.sign_in_button)
        layout.addLayout(self.button_layout)
        layout.addWidget(self.output_label)
        layout.addWidget(self.output_text)
        layout.addWidget(self.progress_label)
        layout.addWidget(self.progress_bar)

        self.scrape_button.clicked.connect(self.scrape_usernames)
        self.save_button.clicked.connect(self.save_usernames)
        self.clear_button.clicked.connect(self.clear_output)
        self.download_all_button.clicked.connect(self.download_all_subscribed_users)

        self.scraper = Scraper()
        self.executor = ThreadPoolExecutor(max_workers=4)  # Adjust the number of workers as needed

    def sign_in_onlyfans(self):
        login_url = "https://onlyfans.com/login"
        QMessageBox.information(self, "Sign In", f"Please sign in to OnlyFans in the opened web browser window:\n{login_url}")

    def scrape_usernames(self):
        input_text = self.url_input.text().strip()
        if not input_text:
            QMessageBox.critical(self, "Error", "No URLs provided.")
            return
        urls = [url.strip() for url in input_text.split(',') if url.strip()]
        if not urls:
            QMessageBox.critical(self, "Error", "No valid URLs provided.")
            return
        app_token = self.scraper.load_auth_info()
        if not app_token:
            QMessageBox.critical(self, "Error", "Failed to load authentication token.")
            return
        headers = {
            "Authorization": f"Bearer {app_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(urls))
        self.progress_bar.setValue(0)
        for url in urls:
            self.executor.submit(self.scrape_usernames_thread, url, headers)

    def scrape_usernames_thread(self, url, headers):
        usernames = self.scraper.scrape_usernames(url, headers)
        self.update_output(f"Scraped Usernames from {url}: {', '.join(usernames)}")
        self.progress_bar.setValue(self.progress_bar.value() + 1)

    def save_usernames(self):
        format_dialog = QMessageBox()
        format_dialog.setText("Select a format for saving:")
        format_dialog.addButton("Text", QMessageBox.TextRole)
        format_dialog.addButton("CSV", QMessageBox.AcceptRole)
        format_dialog.addButton("JSON", QMessageBox.AcceptRole)
        format_dialog.setDefaultButton(QMessageBox.AcceptRole)
        if format_dialog.exec_() == QMessageBox.Reject:
            QMessageBox.critical(self, "Error", "No format selected.")
            return
        selected_button = format_dialog.clickedButton().text().lower()
        if not hasattr(self, 'usernames'):
            QMessageBox.critical(self, "Error", "No usernames scraped yet.")
            return
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        if file_dialog.exec_():
            output_file = file_dialog.selectedFiles()[0]
            if self.scraper.save_data(output_file, self.usernames, format=selected_button):
                QMessageBox.information(self, "Saved Usernames", f"Usernames saved to {output_file}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save usernames.")

    def clear_output(self):
        self.output_text.clear()

    def download_all_subscribed_users(self):
        # Add logic to download all subscribed users here
        pass

    def update_output(self, message):
        self.output_text.append(message)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
