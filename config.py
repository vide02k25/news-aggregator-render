# Configuration for the News Aggregator Application
import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file if it exists

# --- API Keys (Replace with actual keys or use environment variables) ---
# It's recommended to store sensitive keys in environment variables or a secure vault.
# For development, you might need to sign up for free tiers.
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "YOUR_NEWSDATA_API_KEY_HERE")
WORLDNEWS_API_KEY = os.getenv("WORLDNEWS_API_KEY", "YOUR_WORLDNEWS_API_KEY_HERE")
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "YOUR_GNEWS_API_KEY_HERE")

# --- Database Configuration ---
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
INSTANCE_FOLDER_PATH = os.path.join(BASE_DIR, '..', 'instance')
DATABASE_PATH = os.path.join(INSTANCE_FOLDER_PATH, 'news.db')
SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
SQLALCHEMY_TRACK_MODIFICATIONS = False

# --- News Categories ---
# Define the categories required by the user
CATEGORIES = [
    "business",
    "politics",
    "science",
    "technology",
    "sports",
    "education",
    "trends", # Note: 'trends' might require keyword search for some APIs
    "entertainment"
]

# --- API Specific Category Mapping (Optional, if needed) ---
# Example: If an API uses different names
API_CATEGORY_MAPPING = {
    "NewsData.io": {
        "business": "business",
        "politics": "politics",
        "science": "science",
        "technology": "technology",
        "sports": "sports",
        "education": "education", # Requires keyword search
        "trends": "top", # Using 'top' as a proxy, or keyword search
        "entertainment": "entertainment",
        "health": "health", # GNews/NewsAPI/WorldNews have health
        "world": "world" # GNews/NewsData/WorldNews have world/nation
    },
    "WorldNewsAPI": {
        "business": "business",
        "politics": "politics",
        "science": "science",
        "technology": "technology",
        "sports": "sports",
        "education": "education",
        "trends": "lifestyle", # Using 'lifestyle' as a proxy, or keyword search
        "entertainment": "entertainment",
        "health": "health",
        "environment": "environment"
    },
    "GNews": {
        "business": "business",
        "politics": "nation", # Using 'nation' as proxy for politics
        "science": "science",
        "technology": "technology",
        "sports": "sports",
        "education": "general", # Requires keyword search
        "trends": "general", # Requires keyword search
        "entertainment": "entertainment",
        "health": "health",
        "world": "world"
    }
}

# --- Scheduling Configuration ---
# India Standard Time (IST) is UTC+5:30
SCHEDULE_TIMES_IST = ["10:00", "18:00"]
SCHEDULE_TIMEZONE = "Asia/Kolkata"

# --- Other Settings ---
# Max articles to fetch per category per API run (adjust based on API limits)
MAX_ARTICLES_PER_FETCH = 20
# How far back to look for articles (e.g., '1d' for 1 day) - relevant for some APIs
FETCH_LOOKBACK_PERIOD = "1d"

