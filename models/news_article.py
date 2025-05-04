# Database models for the News Aggregator Application
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import sys
import os

# Ensure src directory is in path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base # Import Base from database.py

class NewsArticle(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(Text, nullable=False, unique=True) # Unique constraint on URL
    image_url = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=False)
    source_name = Column(String(255), nullable=True)
    source_url = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    api_source = Column(String(100), nullable=True)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Optional: Add a unique constraint across multiple columns if needed
    # __table_args__ = (UniqueConstraint("url", name="uq_article_url"),)

    def __repr__(self):
        return f"<NewsArticle(id={self.id}, title=\"{self.title[:50]}...\", url=\"{self.url}\")>"

