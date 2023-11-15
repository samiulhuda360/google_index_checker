from celery import shared_task
import time
import requests
import csv
from urllib.parse import urlparse, urlunparse
from .models import UrlIndexStatus
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Access the API key
api_key = os.getenv('API_KEY')


def normalize_url(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.lower()

    # Consistently remove 'www.'
    domain = domain.replace('www.', '')

    # Reconstructing the URL without 'www.'
    normalized_url = f"{parsed_url.scheme}://{domain}{parsed_url.path}"
    return normalized_url.rstrip('/')

def is_url_present_in_search_results(target_url):
    QUERY = f"site:{target_url}"
    API_URL = f"https://api.scrape-it.cloud/scrape/google?location=Austin%2CTexas%2CUnited+States&q={QUERY}&filter=1&domain=google.com&gl=us&hl=en&deviceType=desktop"

    headers = {
        'x-api-key':api_key,
    }

    response = requests.get(API_URL, headers=headers)

    if response.status_code == 200:
        data = response.json()
        if 'organicResults' in data and data['organicResults']:
            organic_results = normalize_url(data['organicResults'][0]['link'])
            normalized_target_url = normalize_url(target_url)
            return "Indexed" if organic_results == normalized_target_url else "Not Indexed"
        else:
            return "Not Indexed"
    else:
        return None

@shared_task
def check_and_save_urls(url_list):
    print(url_list)
    results = []
    for url in url_list:
        normalized_url = normalize_url(url)
        is_indexed = is_url_present_in_search_results(normalized_url)
        # Create and save the model instance
        url_index_status = UrlIndexStatus(url=normalized_url, is_indexed=is_indexed)
        url_index_status.save()
        # For CSV
        results.append((normalized_url, is_indexed))
        time.sleep(5)
    return results
