import PySimpleGUI as sg
from scraper import Scraper
from concurrent.futures import ThreadPoolExecutor

class MainWindow:
    def __init__(self):
        self.scraper = Scraper()
        self.executor = ThreadPoolExecutor(max_workers=4)

        sg.theme("Poppins")
        layout = [
            [sg.Text("Enter URLs (separated by commas):", font=("Poppins", 16), text_color="orange")],
            [sg.InputText(key="-URL_INPUT-", size=(50, 1))],
            [sg.Button("Scrape Usernames", key="-SCRAPE_BUTTON-", size=(20, 1), button_color=("white", "#4A90E2")),
             sg.Button("Scrape Media", key="-MEDIA_BUTTON-", size=(20, 1), button_color=("white", "#4A90E2")),
             sg.Button("Download Media", key="-DOWNLOAD_MEDIA_BUTTON-", size=(20, 1), button_color=("white", "#4A90E2"))],
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
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

    def run(self):
        while True:
            event, values = self.window.read()
            if event == sg.WINDOW_CLOSED:
                break
            elif event == "-SCRAPE_BUTTON-":
                urls = [url.strip() for url in values["-URL_INPUT-"].split(',') if url.strip()]
                if not urls:
                    sg.popup_error("No valid URLs provided.")
                else:
                    self.scrape_usernames(urls)
            elif event == "-MEDIA_BUTTON-":
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

        self.window.close()

def main():
    window = MainWindow()
    window.run()

if __name__ == "__main__":
    main()
