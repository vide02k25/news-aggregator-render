# Main entry point for the Flask News Aggregator app

import sys
import os

# --- DO NOT CHANGE THIS --- #
# Ensure src directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
# -------------------------- #

from flask import Flask, flash # Import flash
from flask_sqlalchemy import SQLAlchemy

# Import configurations and database setup
from config import SQLALCHEMY_DATABASE_URI, SQLALCHEMY_TRACK_MODIFICATIONS, INSTANCE_FOLDER_PATH
from database import Base, engine # Import Base and engine

# Import blueprints
from routes.main_routes import main_bp

# Initialize SQLAlchemy extension object (but don\t bind it to app yet)
db = SQLAlchemy()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, instance_path=INSTANCE_FOLDER_PATH, instance_relative_config=False)

    # Load configuration from config.py
    app.config.from_pyfile("config.py")

    # Override DB URI from config.py (ensure it uses the correct path)
    app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = SQLALCHEMY_TRACK_MODIFICATIONS

    # Add a secret key for session management (required for flash messages)
    # In a real app, use a strong, randomly generated key stored securely.
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

    # Initialize extensions
    db.init_app(app)

    # Create database tables if they don\t exist
    with app.app_context():
        # Import models here so Base knows about them before create_all
        from models.news_article import NewsArticle
        Base.metadata.create_all(bind=engine)
        print("Database tables checked/created.")

    # Register blueprints
    app.register_blueprint(main_bp)

    # Optional: Add a command to manually fetch news
    @app.cli.command("fetch-news")
    def fetch_news_command():
        """CLI command to fetch and store news."""
        print("Starting manual news fetch via CLI...")
        from services.api_clients import fetch_all_news
        from services.processing import process_and_store_articles
        try:
            raw_articles = fetch_all_news()
            if raw_articles:
                process_and_store_articles(raw_articles)
                print("News fetch and processing complete.")
            else:
                print("No new articles fetched.")
        except Exception as e:
            print(f"Error during CLI news fetch: {e}")

    return app

# Create the app instance using the factory
app = create_app()

if __name__ == "__main__":
    # Run the development server
    # Listen on 0.0.0.0 to be accessible externally if needed
    app.run(host="0.0.0.0", port=5000, debug=True) # Use debug=False for production

