import PySimpleGUI as sg
from scraper import Scraper
from concurrent.futures import ThreadPoolExecutor

class MainWindow:
    def __init__(self):
        self.scraper = Scraper()
        self.executor = ThreadPoolExecutor(max_workers=4)

        sg.theme("LightGreen2")
        layout = [
            [sg.Text("Enter URLs (separated by commas):", font=("Poppins", 16), text_color="orange")],
            [sg.InputText(key="-URL_INPUT-", size=(50, 1))],
            [sg.Button("Scrape Usernames", key="-SCRAPE_USERNAMES_BUTTON-", size=(20, 1), button_color=("white", "#4A90E2")),
             sg.Button("Scrape Media", key="-SCRAPE_MEDIA_BUTTON-", size=(20, 1), button_color=("white", "#4A90E2")),
             sg.Button("Download Media", key="-DOWNLOAD_MEDIA_BUTTON-", size=(20, 1), button_color=("white", "#4A90E2"))],
            [sg.Text("Scrape All Subscribed", font=("Poppins", 16), text_color="orange")],
            [sg.Button("Scrape All Subscribed", key="-SCRAPE_ALL_SUBSCRIBED_BUTTON-", size=(20, 1), button_color=("white", "#4A90E2"))],
            [sg.Output(size=(80, 20), key="-OUTPUT-", text_color="orange", background_color="blue", font=("Poppins", 12))],
            [sg.Text("Progress:", font=("Poppins", 16), text_color="orange")],
            [sg.ProgressBar(100, orientation="h", size=(50, 20), key="-PROGRESS_BAR-", visible=False, bar_color=("orange", "blue"))]
        ]

        self.window = sg.Window("OnlyFans Scraper", layout, finalize=True)

    def scrape_usernames(self, urls):
        app_token = self.scraper.load_auth_info()
        if not app_token:
            sg.popup_error("Failed to load authentication token.")
            return
        headers = {
            "Authorization": f"Bearer {app_token}",
            "User-Agent": self.scraper.get_next_user_agent()
        }
        progress_bar = self.window["-PROGRESS_BAR-"]
        progress_bar.update(0, visible=True)
        for url in urls:
            self.executor.submit(self.scraper.scrape_usernames, url, headers)

    def scrape_media(self, urls):
        app_token = self.scraper.load_auth_info()
        if not app_token:
            sg.popup_error("Failed to load authentication token.")
            return
        headers = {
            "Authorization": f"Bearer {app_token}",
            "User-Agent": self.scraper.get_next_user_agent()
        }
        progress_bar = self.window["-PROGRESS_BAR-"]
        progress_bar.update(0, visible=True)
        for url in urls:
            self.executor.submit(self.scraper.scrape_media, url, headers)

    def download_media(self, urls, output_dir):
        progress_bar = self.window["-PROGRESS_BAR-"]
        progress_bar.update(0, visible=True)
        for url in urls:
            self.executor.submit(self.scraper.download_media, url, output_dir)

    def scrape_all_subscribed(self):
        auth_info = self.scraper.load_auth_info()
        if not auth_info:
            sg.popup_error("Failed to load authentication info.")
            return

        # Extract necessary authentication information
        email = auth_info.get("email")
        password = auth_info.get("password")

        if not email or not password:
            sg.popup_error("Incomplete authentication info in auth.json.")
            return

        # Authenticate with OnlyFans
        if not self.scraper.authenticate(email, password):
            sg.popup_error("Failed to authenticate with OnlyFans.")
            return

        # Scrape all subscribed users' content
        self.scraper.scrape_all_subscribed()

        sg.popup("Scraping of all subscribed users' content completed successfully!")

    def run(self):
        while True:
            event, values = self.window.read()
            if event == sg.WINDOW_CLOSED:
                break
            elif event == "-SCRAPE_USERNAMES_BUTTON-":
                urls = [url.strip() for url in values["-URL_INPUT-"].split(',') if url.strip()]
                if not urls:
                    sg.popup_error("No valid URLs provided.")
                else:
                    self.scrape_usernames(urls)
            elif event == "-SCRAPE_MEDIA_BUTTON-":
                urls = [url.strip() for url in values["-URL_INPUT-"].split(',') if url.strip()]
                if not urls:
                    sg.popup_error("No valid URLs provided.")
                else:
                    self.scrape_media(urls)
            elif event == "-DOWNLOAD_MEDIA_BUTTON-":
                urls = [url.strip() for url in values["-URL_INPUT-"].split(',') if url.strip()]
                if not urls:
                    sg.popup_error("No valid URLs provided.")
                else:
                    output_dir = sg.popup_get_folder("Select Output Folder", button_color=("white", "#4A90E2"), background_color="blue")
                    if output_dir:
                        self.download_media(urls, output_dir)
                    else:
                        sg.popup_error("No output folder selected.")
            elif event == "-SCRAPE_ALL_SUBSCRIBED_BUTTON-":
                self.scrape_all_subscribed()

        self.window.close()

def main():
    window = MainWindow()
    window.run()

if __name__ == "__main__":
    main()
