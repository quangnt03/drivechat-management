from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
from .base import Base

class Item(Base):
    """
    Model representing a document item in the system.
    """
    __tablename__ = "items"

    id = Column(String, primary_key=True, index=True)
    file_name = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    uri = Column(String, nullable=False)
    conversation_id = Column(String, nullable=False)
    owner = Column(String, nullable=False)
    last_updated = Column(DateTime(timezone=True), onupdate=func.now())
    active = Column(Boolean, default=True)

    def __repr__(self):
        return f"<Item(id={self.id}, file_name='{self.file_name}')>" 