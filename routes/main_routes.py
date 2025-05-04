# Flask routes for the News Aggregator Application

from flask import Blueprint, render_template, abort, redirect, url_for, flash
from sqlalchemy import desc
from datetime import datetime, timedelta
import sys
import os
import logging

# Ensure src directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import get_db
from models.news_article import NewsArticle
from config import CATEGORIES
from services.api_clients import fetch_all_news
from services.processing import process_and_store_articles

# Create a Blueprint
main_bp = Blueprint("main", __name__)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@main_bp.route("/")
def index():
    """Displays the main page with headlines grouped by category."""
    db = next(get_db()) # Get a database session
    try:
        # Fetch recent articles (e.g., fetched in the last 24 hours)
        # Adjust timedelta as needed
        twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
        recent_articles = db.query(NewsArticle)\
                            .filter(NewsArticle.fetched_at >= twenty_four_hours_ago)\
                            .order_by(desc(NewsArticle.published_at))\
                            .all()

        # Group articles by category
        articles_by_category = {category: [] for category in CATEGORIES}
        for article in recent_articles:
            # Use the category stored in the DB, which should align with CATEGORIES
            if article.category in articles_by_category:
                articles_by_category[article.category].append(article)
            # Optional: Add articles with unknown/other categories to a default list
            # elif "other" in articles_by_category:
            #     articles_by_category["other"].append(article)

        # Remove categories with no articles to avoid empty sections
        articles_by_category = {k: v for k, v in articles_by_category.items() if v}

    finally:
        db.close()

    return render_template("index.html", articles_by_category=articles_by_category)

@main_bp.route("/article/<int:article_id>")
def article_detail(article_id):
    """Displays the detailed view for a single article."""
    db = next(get_db())
    try:
        article = db.query(NewsArticle).get(article_id)
    finally:
        db.close()

    if article is None:
        abort(404) # Not found

    return render_template("article.html", article=article)

@main_bp.route("/update", methods=["POST"]) # Use POST to prevent accidental triggers via GET
def trigger_update():
    """Manually triggers the news fetching and processing."""
    logging.info("Manual update triggered.")
    try:
        # Step 1: Fetch news from all APIs
        raw_articles = fetch_all_news()

        # Step 2: Process and store the fetched articles
        if raw_articles:
            process_and_store_articles(raw_articles)
            flash(f"News update complete. Processed articles.", "success")
        else:
            flash("News update ran, but no new articles were fetched.", "info")

    except Exception as e:
        logging.error(f"Error during manual update: {e}")
        flash(f"An error occurred during the update process: {e}", "error")

    return redirect(url_for("main.index")) # Redirect back to the homepage

