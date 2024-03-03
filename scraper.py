import PySimpleGUI as sg
import logging
import json
import os
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from itertools import cycle
import random

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

        # Configure logging
        logging.basicConfig(filename='error.log', level=logging.ERROR)

    def scrape_with_retry(self, url, headers):
        retry_strategy = requests.packages.urllib3.util.retry.Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
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
            logging.exception("An error occurred while scraping usernames: %s", e)

    def scrape_media(self, url, headers):
        try:
            response = self.scrape_with_retry(url, headers)
            soup = BeautifulSoup(response.content, 'html.parser')
            self.media_urls = [media['src'] for media in soup.find_all('img', class_='media')]
            # Add logic for other media types like videos here
        except requests.exceptions.RequestException as e:
            logging.exception("An error occurred while scraping media: %s", e)

    def download_media(self, url, output_dir):
        try:
            response = self.scrape_with_retry(url, headers={})
            response.raise_for_status()
            filename = os.path.basename(url)
            with open(os.path.join(output_dir, filename), 'wb') as file:
                file.write(response.content)
            print(f"Downloaded: {url}")
        except requests.exceptions.RequestException as e:
            logging.exception("An error occurred while downloading media: %s", e)

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
            logging.exception("An error occurred while saving data: %s", e)
            return False

    def load_auth_info(self):
        try:
            with open("auth.json", "r") as file:
                auth_info = json.load(file)
            auth = auth_info.get('auth')
            if auth is None:
                logging.error("Authentication information is missing from auth.json")
            return auth
        except FileNotFoundError:
            logging.error("Authentication file not found.")
            return None
        except json.JSONDecodeError:
            logging.error("Error decoding authentication file.")
            return None

    def save_auth_info(self, auth_info):
        try:
            with open("auth.json", "w") as file:
                json.dump({'auth': auth_info}, file, indent=4)
            print("Authentication info saved.")
        except Exception as e:
            logging.exception("An error occurred while saving auth info: %s", e)

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
            [sg.Text("Scrape All Pics and Vids of:", font=("Poppins", 16), text_color="orange")],
            [sg.InputText(key="-USERNAME_INPUT-", size=(50, 1))],
            [sg.Button("Scrape User Pics and Vids", key="-SCRAPE_USER_MEDIA_BUTTON-", size=(20, 1), button_color=("white", "#4A90E2"))],
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
            "Authorization": f"Bearer {app_token.get('app-token')}",
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
            "Authorization": f"Bearer {app_token.get('app-token')}",
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

    def scrape_user_media(self, username):
        app_token = self.scraper.load_auth_info()
        if not app_token:
            sg.popup_error("Failed to load authentication token.")
            return
        headers = {
            "Authorization": f"Bearer {app_token.get('app-token')}",
            "User-Agent": self.scraper.get_next_user_agent()
        }
        progress_bar = self.window["-PROGRESS_BAR-"]
        progress_bar.update(0, visible=True)
        # Implement logic to scrape all pics and vids of the given username

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
            elif event == "-SCRAPE_USER_MEDIA_BUTTON-":
                username = values["-USERNAME_INPUT-"].strip()
                if not username:
                    sg.popup_error("Please enter a valid username.")
                else:
                    self.scrape_user_media(username)

        self.window.close()

def main():
    window = MainWindow()
    window.run()

if __name__ == "__main__":
    main()
