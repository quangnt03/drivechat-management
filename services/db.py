from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.base import Base
from sqlalchemy.sql import text
import logging

class DatabaseService:
    def __init__(self, db_url: str):
        """
        Initialize database connection and create tables.
        
        Args:
            db_url (str): Database connection URL
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.engine = create_engine(db_url)
        
        # Create all tables before creating the session
        try:
            # Enable pgvector extension
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
                conn.commit()
            
            # Create all tables defined in the models
            Base.metadata.create_all(bind=self.engine)
            
        except Exception as e:
            self.logger.error(f"Failed to create database tables: {str(e)}")
            raise
        
        # Create session factory
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.session = self.SessionLocal()
