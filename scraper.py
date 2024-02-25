import os
import json
import requests
from bs4 import BeautifulSoup
from PySide6.QtWidgets import QMessageBox


class Scraper:
    def __init__(self):
        self.usernames = []
        self.media_urls = []

    def scrape_usernames(self, url, headers):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                self.usernames = [user.text for user in soup.find_all(class_='username')]
            else:
                print(f"Failed to fetch URL: {url}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error scraping usernames: {e}")

    def scrape_media(self, url, headers):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                self.media_urls = [media['src'] for media in soup.find_all('img', class_='media')]
            else:
                print(f"Failed to fetch URL: {url}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error scraping media: {e}")

    def download_media(self, url, output_dir):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                filename = os.path.basename(url)
                with open(os.path.join(output_dir, filename), 'wb') as file:
                    file.write(response.content)
                print(f"Downloaded: {url}")
            else:
                print(f"Failed to download {url}. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")

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
        except Exception as e:
            print(f"Error loading auth info: {e}")
            return None

    def save_auth_info(self, auth_info):
        try:
            with open("auth.json", "w") as file:
                json.dump(auth_info, file, indent=4)
            print("Authentication info saved.")
        except Exception as e:
            print(f"Error saving auth info: {e}")

