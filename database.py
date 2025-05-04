# Database setup for the News Aggregator Application
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import sys

# Ensure src directory is in path for imports
sys.path.insert(0, os.path.dirname(__file__))

from config import SQLALCHEMY_DATABASE_URI, INSTANCE_FOLDER_PATH

# Ensure the instance folder exists
if not os.path.exists(INSTANCE_FOLDER_PATH):
    os.makedirs(INSTANCE_FOLDER_PATH)

# Define the base for declarative models
Base = declarative_base()

# Create the SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URI)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency function to get a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes the database by creating tables based on models."""
    # Import all modules here that might define models so that
    # they will be registered properly on the metadata. Otherwise
    # you will have to import them first before calling init_db()
    # Base.metadata.create_all(bind=engine) # This line is moved to main.py
    # to ensure models are loaded before table creation.
    print(f"Database initialization check. Tables should be created via Flask app context.")
    print(f"Database file should be at: {SQLALCHEMY_DATABASE_URI}")

# You might run this script directly to initialize the DB manually if needed,
# but it's better integrated into the Flask app startup.
# if __name__ == "__main__":
#     print("Initializing database...")
#     # Import models here if running standalone
#     from models.news_article import NewsArticle
#     Base.metadata.create_all(bind=engine)
#     print("Database initialized.")

