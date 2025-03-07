from .base import Base
from .item import Item
from .embedding import Embedding
import models.relationships  # This will set up the relationships

__all__ = ['Base', 'Item', 'Embedding']