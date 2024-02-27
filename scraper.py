import os
import json
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from itertools import cycle
import random
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import datetime

class Scraper:
    def __init__(self, proxies=None):
        self.usernames = []
        self.media_urls = []
        self.proxies = proxies
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        ]
        self.user_agent_cycle = cycle(self.user_agents)

    def scrape_with_retry(self, url, headers):
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        with requests.Session() as session:
            session.mount("https://", adapter)
            session.mount("http://", adapter)
            response = session.get(url, headers=headers, proxies=self.proxies)
            response.raise_for_status()
            return response

    def scrape_usernames(self, url, headers):
        try:
            response = self.scrape_with_retry(url, headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            self.usernames = [user.text for user in soup.find_all(class_='username')]
        except requests.exceptions.RequestException as e:
            print(f"Error scraping usernames from {url}: {e}")

    def scrape_media(self, url, headers):
        try:
            response = self.scrape_with_retry(url, headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            self.media_urls = [media['src'] for media in soup.find_all('img', class_='media')]
            # Add logic for other media types like videos here
        except requests.exceptions.RequestException as e:
            print(f"Error scraping media from {url}: {e}")

    def download_media(self, url, output_dir):
        try:
            response = self.scrape_with_retry(url, headers={})
            response.raise_for_status()
            filename = os.path.basename(url)
            with open(os.path.join(output_dir, filename), 'wb') as file:
                file.write(response.content)
            print(f"Downloaded: {url}")
        except requests.exceptions.RequestException as e:
            print(f"Error downloading {url}: {e}")

    def get_random_user_agent(self):
        return random.choice(self.user_agents)

    def get_next_user_agent(self):
        return next(self.user_agent_cycle)

    def set_proxies(self, proxies):
        self.proxies = proxies

    def save_data(self, output_dir, data, format):
        try:
            if format == "text":
                with open(os.path.join(output_dir, "scraped_data.txt"), "w") as file:
                    file.write("\n".join(data))
            elif format == "json":
                with open(os.path.join(output_dir, "scraped_data.json"), "w") as file:
                    json.dump(data, file, indent=4)
            else:
                return False
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def load_auth_info(self):
        try:
            with open("auth.json", "r") as file:
                auth_info = json.load(file)
            return auth_info
        except FileNotFoundError:
            print("Authentication file not found.")
            return None
        except json.JSONDecodeError:
            print("Error decoding authentication file.")
            return None

    def save_auth_info(self, auth_info):
        try:
            with open("auth.json", "w") as file:
                json.dump(auth_info, file, indent=4)
            print("Authentication info saved.")
        except Exception as e:
            print(f"Error saving auth info: {e}")

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
