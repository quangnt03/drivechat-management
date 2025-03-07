"""
This module sets up relationships between models after they are defined
to avoid circular import dependencies.
"""
from sqlalchemy.orm import relationship
from .item import Item
from .embedding import Embedding

# Set up Item-Embedding relationship
Item.embeddings = relationship(
    "Embedding",
    back_populates="item",
    cascade="all, delete-orphan",
    lazy="dynamic"
)

Embedding.item = relationship(
    "Item",
    back_populates="embeddings"
) 