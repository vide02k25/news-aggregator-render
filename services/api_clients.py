# Functions to interact with various News APIs

import requests
import logging
from datetime import datetime, timedelta
import sys
import os

# Ensure src directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import (
    NEWSDATA_API_KEY,
    WORLDNEWS_API_KEY,
    GNEWS_API_KEY,
    MAX_ARTICLES_PER_FETCH,
    API_CATEGORY_MAPPING,
    CATEGORIES
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Helper Functions ---

def get_api_category(api_name, general_category):
    """Maps a general category to the API-specific category name."""
    if api_name in API_CATEGORY_MAPPING and general_category in API_CATEGORY_MAPPING[api_name]:
        return API_CATEGORY_MAPPING[api_name][general_category]
    # Fallback if mapping doesn\t exist or category not listed for that API
    # Use the general category name directly or handle as keyword search later
    return general_category

def requires_keyword_search(api_name, general_category):
    """Checks if a category likely requires a keyword search for a specific API."""
    # Simple check based on known limitations or specific mappings
    if api_name == "NewsData.io" and general_category in ["education", "trends"]:
        return True
    if api_name == "WorldNewsAPI" and general_category == "trends": # Assuming lifestyle isn\t a perfect match
        return True
    if api_name == "GNews" and general_category in ["politics", "education", "trends"]:
        return True
    return False

# --- API Client Functions ---

def fetch_newsdata_io(category):
    """Fetches news from NewsData.io API."""
    api_name = "NewsData.io"
    api_category = get_api_category(api_name, category)
    use_keyword = requires_keyword_search(api_name, category)

    base_url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": NEWSDATA_API_KEY,
        "language": "en",
        # "country": "in", # Can add country filter if needed
        "size": MAX_ARTICLES_PER_FETCH
    }

    if use_keyword:
        params["q"] = category # Use category name as keyword
        logging.info(f"[{api_name}] Using keyword search for category: {category}")
    else:
        params["category"] = api_category
        logging.info(f"[{api_name}] Fetching category: {api_category} (mapped from {category})")

    try:
        response = requests.get(base_url, params=params, timeout=20)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        if data.get("status") == "success":
            logging.info(f"[{api_name}] Successfully fetched {len(data.get('results', []))} articles for category: {category}")
            return data.get("results", [])
        else:
            logging.error(f"[{api_name}] API error for category {category}: {data.get('results', {}).get('message')}")
            return []
    except requests.exceptions.RequestException as e:
        logging.error(f"[{api_name}] Request failed for category {category}: {e}")
        return []
    except Exception as e:
        logging.error(f"[{api_name}] Unexpected error for category {category}: {e}")
        return []

def fetch_worldnewsapi(category):
    """Fetches news from World News API."""
    api_name = "WorldNewsAPI"
    api_category = get_api_category(api_name, category)
    use_keyword = requires_keyword_search(api_name, category)

    base_url = "https://api.worldnewsapi.com/search-news"
    params = {
        "api-key": WORLDNEWS_API_KEY,
        "language": "en",
        # "source-countries": "in", # Can add country filter
        "number": MAX_ARTICLES_PER_FETCH,
        "sort": "publish-time",
        "sort-direction": "DESC"
    }

    if use_keyword:
        params["text"] = category # Use category name as keyword
        logging.info(f"[{api_name}] Using keyword search for category: {category}")
    else:
        params["category-filter"] = api_category
        logging.info(f"[{api_name}] Fetching category: {api_category} (mapped from {category})")

    try:
        response = requests.get(base_url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        # WorldNewsAPI doesn\t seem to have a top-level status field in the same way
        # Assume success if no exception and data is present
        articles = data.get("news", [])
        logging.info(f"[{api_name}] Successfully fetched {len(articles)} articles for category: {category}")
        return articles
    except requests.exceptions.RequestException as e:
        logging.error(f"[{api_name}] Request failed for category {category}: {e}")
        return []
    except Exception as e:
        logging.error(f"[{api_name}] Unexpected error for category {category}: {e}")
        return []

def fetch_gnews(category):
    """Fetches news from GNews API."""
    api_name = "GNews"
    api_category = get_api_category(api_name, category)
    use_keyword = requires_keyword_search(api_name, category)

    # GNews uses different endpoints for category vs keyword
    if use_keyword:
        base_url = "https://gnews.io/api/v4/search"
        params = {
            "q": category,
            "apikey": GNEWS_API_KEY,
            "lang": "en",
            # "country": "in",
            "max": MAX_ARTICLES_PER_FETCH,
            "sortby": "publishedAt"
        }
        logging.info(f"[{api_name}] Using keyword search for category: {category}")
    else:
        base_url = "https://gnews.io/api/v4/top-headlines"
        params = {
            "category": api_category,
            "apikey": GNEWS_API_KEY,
            "lang": "en",
            # "country": "in",
            "max": MAX_ARTICLES_PER_FETCH,
            "sortby": "publishedAt"
        }
        logging.info(f"[{api_name}] Fetching category: {api_category} (mapped from {category})")

    try:
        response = requests.get(base_url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        # GNews also doesn\t seem to have a top-level status, relies on HTTP status
        articles = data.get("articles", [])
        logging.info(f"[{api_name}] Successfully fetched {len(articles)} articles for category: {category}")
        return articles
    except requests.exceptions.RequestException as e:
        logging.error(f"[{api_name}] Request failed for category {category}: {e}")
        return []
    except Exception as e:
        logging.error(f"[{api_name}] Unexpected error for category {category}: {e}")
        return []

# --- Main Fetching Orchestration (Example Usage) ---

def fetch_all_news():
    """Fetches news from all configured APIs and categories."""
    all_articles = []
    api_functions = {
        "NewsData.io": fetch_newsdata_io,
        "WorldNewsAPI": fetch_worldnewsapi,
        "GNews": fetch_gnews
    }

    for category in CATEGORIES:
        logging.info(f"--- Fetching category: {category} ---")
        for api_name, fetch_func in api_functions.items():
            articles = fetch_func(category)
            if articles:
                # Add api_name to each article for processing step
                for article in articles:
                    article["_api_source"] = api_name
                    article["_query_category"] = category # Store the original category query
                all_articles.extend(articles)
            # Consider adding a small delay here if hitting rate limits
            # time.sleep(1)

    logging.info(f"Total articles fetched across all APIs/categories: {len(all_articles)}")
    return all_articles

# Example of running the fetch directly (for testing)
# if __name__ == "__main__":
#     fetched_data = fetch_all_news()
#     # You would typically pass fetched_data to the processing functions next
#     print(f"Fetched {len(fetched_data)} articles in total.")
#     # print(fetched_data[:2]) # Print first few articles for inspection

