# Functions to process and store fetched news articles

import logging
from datetime import datetime
from dateutil import parser as date_parser # Use dateutil for robust parsing
import sys
import os

# Ensure src directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import SessionLocal, engine, Base
from models.news_article import NewsArticle
from config import CATEGORIES # Import categories if needed for assignment

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# --- Helper Functions ---

def parse_datetime(date_string):
    """Parses various date string formats into UTC datetime objects."""
    if not date_string:
        return None
    try:
        # Use dateutil.parser.isoparse for ISO 8601 formats primarily
        # It handles timezone offsets like Z or +00:00 correctly
        dt = date_parser.isoparse(date_string)
        # Ensure the datetime object is timezone-aware and convert to UTC
        if dt.tzinfo is None:
            # If no timezone info, assume UTC (or make a different assumption if needed)
            # This is less ideal; APIs should provide timezone info.
            # dt = dt.replace(tzinfo=pytz.utc)
            # For simplicity without adding pytz dependency here, we might rely on APIs providing TZ
            # Or just store as naive, assuming UTC if not specified
            logging.warning(f"Parsed datetime '{date_string}' has no timezone info. Assuming UTC.")
            # Let\s just return the naive datetime for now, assuming DB stores it okay.
            # Or better, use default=datetime.utcnow in the model if parsing fails.
            return dt # Return naive
        else:
            return dt.astimezone(datetime.timezone.utc)
    except ValueError:
        try:
            # Fallback to generic dateutil.parser.parse for other formats
            dt = date_parser.parse(date_string)
            if dt.tzinfo is None:
                logging.warning(f"Fallback parsed datetime '{date_string}' has no timezone info. Assuming UTC.")
                return dt # Return naive
            else:
                return dt.astimezone(datetime.timezone.utc)
        except Exception as e:
            logging.error(f"Could not parse date string: {date_string} - Error: {e}")
            return None
    except Exception as e:
        logging.error(f"Could not parse date string (isoparse): {date_string} - Error: {e}")
        return None

# --- Standardization Functions ---

def standardize_newsdata(article, query_category):
    """Standardizes an article from NewsData.io."""
    published_dt = parse_datetime(article.get("pubDate"))
    if not published_dt:
        published_dt = datetime.utcnow() # Fallback

    return {
        "title": article.get("title"),
        "description": article.get("description"),
        "content": article.get("content"),
        "url": article.get("link"),
        "image_url": article.get("image_url"),
        "published_at": published_dt,
        "source_name": article.get("source_id"), # NewsData uses source_id
        "source_url": None, # NewsData doesn\t seem to provide source homepage URL directly
        "category": article.get("category", [query_category])[0] if article.get("category") else query_category, # Use API category or fallback
        "api_source": "NewsData.io"
    }

def standardize_worldnews(article, query_category):
    """Standardizes an article from World News API."""
    published_dt = parse_datetime(article.get("publish_date"))
    if not published_dt:
        published_dt = datetime.utcnow() # Fallback

    return {
        "title": article.get("title"),
        "description": article.get("text"), # WorldNews seems to use \'text\' for description/summary
        "content": article.get("text"), # Use text again, might be same as description
        "url": article.get("url"),
        "image_url": article.get("image"),
        "published_at": published_dt,
        "source_name": article.get("source_country"), # Using country as source name proxy
        "source_url": None, # No obvious source homepage URL
        "category": query_category, # WorldNews doesn\t return category in search results
        "api_source": "WorldNewsAPI"
    }

def standardize_gnews(article, query_category):
    """Standardizes an article from GNews API."""
    published_dt = parse_datetime(article.get("publishedAt"))
    if not published_dt:
        published_dt = datetime.utcnow() # Fallback

    return {
        "title": article.get("title"),
        "description": article.get("description"),
        "content": article.get("content"),
        "url": article.get("url"),
        "image_url": article.get("image"),
        "published_at": published_dt,
        "source_name": article.get("source", {}).get("name"),
        "source_url": article.get("source", {}).get("url"),
        "category": query_category, # GNews doesn\t return category in search results
        "api_source": "GNews"
    }

# --- Main Processing Function ---

def process_and_store_articles(raw_articles):
    """Processes raw articles, standardizes them, and stores unique ones in the DB."""
    if not raw_articles:
        logging.info("No articles fetched to process.")
        return

    db = SessionLocal()
    added_count = 0
    skipped_count = 0
    processed_urls = set(item[0] for item in db.query(NewsArticle.url).all()) # Load existing URLs

    standardization_map = {
        "NewsData.io": standardize_newsdata,
        "WorldNewsAPI": standardize_worldnews,
        "GNews": standardize_gnews
    }

    try:
        for raw_article in raw_articles:
            api_source = raw_article.get("_api_source")
            query_category = raw_article.get("_query_category", "general") # Get category used in query

            if not api_source or api_source not in standardization_map:
                logging.warning(f"Skipping article with unknown or unsupported API source: {api_source}")
                continue

            standardizer = standardization_map[api_source]
            try:
                standardized_data = standardizer(raw_article, query_category)
            except Exception as e:
                logging.error(f"Failed to standardize article from {api_source}: {e} - Data: {raw_article}")
                continue

            # Basic validation
            if not standardized_data.get("url") or not standardized_data.get("title"):
                logging.warning(f"Skipping article from {api_source} due to missing URL or title.")
                continue

            article_url = standardized_data["url"]

            # Check for duplicates using the in-memory set and database check
            if article_url in processed_urls:
                skipped_count += 1
                continue

            # Check DB again just in case (though set should be sufficient if loaded correctly)
            # exists = db.query(NewsArticle.id).filter(NewsArticle.url == article_url).first()
            # if exists:
            #     skipped_count += 1
            #     processed_urls.add(article_url) # Ensure set is updated
            #     continue

            # Create NewsArticle object
            try:
                news_item = NewsArticle(
                    title=standardized_data["title"],
                    description=standardized_data.get("description"),
                    content=standardized_data.get("content"),
                    url=article_url,
                    image_url=standardized_data.get("image_url"),
                    published_at=standardized_data["published_at"],
                    source_name=standardized_data.get("source_name"),
                    source_url=standardized_data.get("source_url"),
                    category=standardized_data.get("category", query_category), # Use standardized or query category
                    api_source=api_source,
                    fetched_at=datetime.utcnow()
                )
                db.add(news_item)
                processed_urls.add(article_url) # Add to set to prevent adding duplicates from the same batch
                added_count += 1
            except Exception as e:
                 logging.error(f"Error creating NewsArticle object for URL {article_url}: {e}")
                 skipped_count += 1 # Count as skipped if creation fails

            # Commit periodically to avoid large transactions (optional)
            # if added_count % 50 == 0:
            #     db.commit()
            #     logging.info("Committed batch of 50 articles.")

        db.commit() # Commit any remaining changes
        logging.info(f"Processing complete. Added: {added_count}, Skipped (duplicates/errors): {skipped_count}")

    except Exception as e:
        logging.error(f"An error occurred during article processing: {e}")
        db.rollback() # Rollback in case of error during the loop
    finally:
        db.close()

# Example of running the processing directly (for testing)
# if __name__ == "__main__":
#     # Create dummy data matching the output of fetch_all_news()
#     dummy_raw_articles = [
#         {
#             "_api_source": "GNews",
#             "_query_category": "technology",
#             "title": "Test GNews Article",
#             "description": "Description here",
#             "content": "Content here",
#             "url": "http://example.com/gnews1",
#             "image": "http://example.com/image.jpg",
#             "publishedAt": "2025-05-01T10:00:00Z",
#             "source": {"name": "GSource", "url": "http://example.com"}
#         },
#         {
#             "_api_source": "NewsData.io",
#             "_query_category": "business",
#             "title": "Test NewsData Article",
#             "description": "Description 2",
#             "content": "Content 2",
#             "link": "http://example.com/newsdata1",
#             "image_url": "http://example.com/image2.jpg",
#             "pubDate": "2025-05-01 09:30:00", # Example different format
#             "source_id": "ndsource",
#             "category": ["business"]
#         },
#         {
#             "_api_source": "WorldNewsAPI",
#             "_query_category": "politics",
#             "title": "Test WorldNews Article",
#             "text": "Description/Content 3",
#             "url": "http://example.com/worldnews1",
#             "image": "http://example.com/image3.jpg",
#             "publish_date": "2025-05-01T08:00:00+0000",
#             "source_country": "us"
#         },
#         {
#             "_api_source": "GNews", # Duplicate URL
#             "_query_category": "technology",
#             "title": "Test GNews Article Duplicate",
#             "description": "Description here",
#             "content": "Content here",
#             "url": "http://example.com/gnews1",
#             "image": "http://example.com/image.jpg",
#             "publishedAt": "2025-05-01T10:05:00Z",
#             "source": {"name": "GSource", "url": "http://example.com"}
#         }
#     ]
#     print("Initializing DB for processing test...")
#     Base.metadata.create_all(bind=engine) # Ensure table exists
#     print("Processing dummy articles...")
#     process_and_store_articles(dummy_raw_articles)
#     print("Processing test finished.")

