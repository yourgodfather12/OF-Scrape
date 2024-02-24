import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox, QTextEdit, QFileDialog, QProgressBar, QLabel, QLineEdit
from scraper import scrape_usernames, save_usernames, load_auth_token
import threading

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OnlyFans Username Scraper")
        self.setGeometry(100, 100, 600, 400)

        # Set the dark theme stylesheet
        self.setStyleSheet(
            "QMainWindow {background-color: #333333; color: #ffffff;}"
            "QPushButton {background-color: #666666; color: #ffffff; border-radius: 5px;}"
            "QPushButton:hover {background-color: #888888;}"
            "QTextEdit {background-color: #444444; color: #ffffff; border-radius: 5px;}"
            "QProgressBar {background-color: #666666; color: #ffffff; border-radius: 5px;}"
            "QLabel {color: #ffffff;}"
            "QLineEdit {background-color: #444444; color: #ffffff; border-radius: 5px;}"
        )

        # Create a central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add URL input field for batch processing
        self.url_label = QLabel("Enter URLs (separated by commas):")
        self.url_input = QLineEdit()

        # Create buttons for scraping, saving, and clearing
        self.scrape_button = QPushButton("Scrape Usernames")
        self.save_button = QPushButton("Save Usernames")
        self.clear_button = QPushButton("Clear Output")
        self.output_text = QTextEdit()
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        layout.addWidget(self.url_label)
        layout.addWidget(self.url_input)
        layout.addWidget(self.scrape_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.output_text)
        layout.addWidget(self.progress_bar)

        # Connect button signals to slots
        self.scrape_button.clicked.connect(self.scrape_usernames)
        self.save_button.clicked.connect(self.save_usernames)
        self.clear_button.clicked.connect(self.clear_output)

    def scrape_usernames(self):
        # Get the input text from the URL field
        input_text = self.url_input.text().strip()

        # Check if the input text is empty
        if not input_text:
            QMessageBox.critical(self, "Error", "No URLs provided.")
            return

        # Split the input text by commas to get individual URLs
        urls = [url.strip() for url in input_text.split(',')]

        # Remove empty strings from the list of URLs
        urls = [url for url in urls if url]

        # Check if there are any valid URLs
        if not urls:
            QMessageBox.critical(self, "Error", "No valid URLs provided.")
            return

        # Load authentication token
        app_token = load_auth_token()

        if not app_token:
            QMessageBox.critical(self, "Error", "Failed to load authentication token.")
            return

        # Set up headers with authentication token and spoofed user-agent
        headers = {
            "Authorization": f"Bearer {app_token}",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        }

        # Show progress bar
        self.progress_bar.setVisible(True)

        # Scrape usernames in a separate thread for each URL
        for url in urls:
            threading.Thread(target=self.scrape_usernames_thread, args=(url, headers)).start()

    def scrape_usernames_thread(self, url, headers):
        # Scrape usernames
        usernames = scrape_usernames(url, headers)

        # Display scraped usernames in output text
        self.output_text.append(f"URL: {url}")
        self.output_text.append("\n".join(usernames))
        self.output_text.append("-----------------------------------")

    def save_usernames(self):
        # Prompt user to select a format for saving
        format_dialog = QMessageBox()
        format_dialog.setText("Select a format for saving:")
        format_dialog.addButton("Text", QMessageBox.TextRole)
        format_dialog.addButton("CSV", QMessageBox.AcceptRole)
        format_dialog.addButton("JSON", QMessageBox.AcceptRole)
        format_dialog.setDefaultButton(QMessageBox.AcceptRole)
        format_dialog.exec_()
        selected_button = format_dialog.clickedButton()

        if selected_button:
            selected_text = selected_button.text().lower()
        else:
            QMessageBox.critical(self, "Error", "No format selected.")
            return

        if not hasattr(self, 'usernames'):
            QMessageBox.critical(self, "Error", "No usernames scraped yet.")
            return

        # Prompt user to select a file for saving
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptSave)
        if file_dialog.exec_():
            output_file = file_dialog.selectedFiles()[0]

            # Save usernames to the selected file
            if save_usernames(self.usernames, output_file, format=selected_text):
                QMessageBox.information(self, "Saved Usernames", f"Usernames saved to {output_file}")
            else:
                QMessageBox.critical(self, "Error", "Failed to save usernames.")

    def clear_output(self):
        self.output_text.clear()

def main():
    app = QApplication(sys.argv)

    # Set the application style to Fusion to ensure consistent styling across platforms
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
