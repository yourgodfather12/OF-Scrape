import requests
import json
import logging
import csv
import threading
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)


def load_auth_token():
    """Load authentication token from auth.json."""
    try:
        with open("auth.json", "r") as auth_file:
            auth_data = json.load(auth_file)
            return auth_data.get("auth", {}).get("app-token")
    except FileNotFoundError:
        logging.error("Auth token file not found.")
        return None
    except json.JSONDecodeError:
        logging.error("Failed to decode auth token file.")
        return None


def scrape_usernames(url, headers, progress_callback=None):
    """Scrape usernames from the specified URL."""
    try:
        # Create a session with retry logic
        session = requests.Session()
        retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        session.mount("https://", HTTPAdapter(max_retries=retries))

        # Send a GET request to the URL with headers
        response = session.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes

        # Parse the HTML content
        soup = BeautifulSoup(response.content, "html.parser")

        # Find all elements matching the specified selector
        usernames = soup.select(
            "#content > div.l-container > div.l-main-content.m-r-side > div.g-sides-gaps.g-page-content > div.b-grid-users > div > div > div.vue-recycle-scroller__item-wrapper > div > div > div > div > div.b-profile__user.m-inside-modelcard > div > div.b-profile__names.mw-0 > div:nth-child(2) > a > div")

        # Extract and return the usernames
        scraped_usernames = [username.text.strip() for username in usernames]

        # Call progress callback if provided
        if progress_callback:
            progress_callback(len(scraped_usernames))

        return scraped_usernames
    except requests.RequestException as e:
        logging.error(f"Failed to scrape usernames: {e}")
        return []


def save_usernames(usernames, output_file, format='txt'):
    """Save usernames to a file."""
    try:
        if format == 'txt':
            with open(output_file, "w") as file:
                for username in usernames:
                    file.write(username + "\n")
        elif format == 'csv':
            with open(output_file, "w", newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Username"])
                for username in usernames:
                    writer.writerow([username])
        elif format == 'json':
            with open(output_file, "w") as jsonfile:
                json.dump(usernames, jsonfile, indent=4)
        else:
            logging.error("Invalid format specified for saving.")
            return False

        logging.info(f"Usernames saved to {output_file}")
        return True
    except IOError as e:
        logging.error(f"Failed to save usernames: {e}")
        return False


def print_usernames(usernames):
    """Print usernames to the console."""
    for username in usernames:
        print(username)
