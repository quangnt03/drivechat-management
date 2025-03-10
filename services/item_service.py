from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from models.item import Item
from models.user import User
from models.conversation import Conversation
from typing import List, Optional
from datetime import datetime

class ItemService:
    def __init__(self, session: Session):
        self.session = session

    def get_item_by_id(self, owner: User, item_id: str) -> Optional[Item]:
        """Get a single item by ID"""
        filters = [Item.id == item_id, Item.owner_id == owner.id]
        query = self.session.query(Item).filter(*filters)
        item = query.first()
        return item


    def get_items_by_owner(self, owner: User, active_only: bool = True) -> List[Item]:
        """
        Get all items for a specific owner
        
        Args:
            owner (str): Owner of the items
            active_only (bool): If True, return only active items. If False, return all items
        """
        query = self.session.query(Item).filter(Item.owner_id == owner.id)
        if active_only:
            query = query.filter(Item.active)
        return query.all()

    def get_items_by_conversation(self, conversation: Conversation, active_only: bool = True) -> List[Item]:
        """Get all items in a specific conversation"""
        query = self.session.query(Item).filter(Item.conversation_id == conversation.id)
        if active_only:
            query = query.filter(Item.active)
        return query.all()

    def search_items(self, 
                    search_term: str, 
                    owner: User,
                    mime_type: Optional[str] = None,
                    active_only: bool = True) -> List[Item]:
        """
        Search items with various filters
        """
        filters = []
        filters.append(Item.owner_id == owner.id)
        
        # Add search term filter (searches in file_name)
        if search_term:
            filters.append(Item.file_name.ilike(f"%{search_term}%"))

        # Add mime type filter if provided
        if mime_type:
            filters.append(Item.mime_type == mime_type)
            
        # Add active filter if requested
        if active_only:
            filters.append(Item.active)
            
        # Combine all filters with AND
        query = self.session.query(Item)
        if filters:
            query = query.filter(and_(*filters))
            
        return query.all()

    def get_recent_items(self, limit: int = 10, owner: Optional[str] = None) -> List[Item]:
        """Get recently updated items"""
        query = self.session.query(Item)
        if owner:
            query = query.filter(Item.owner == owner)
        return query.order_by(desc(Item.last_updated)).limit(limit).all()

    def create_item(self, 
                   file_name: str,
                   mime_type: str,
                   uri: str,
                   owner: str,
                   conversation_id: str) -> Item:
        """Create a new item"""
        item = Item(
            file_name=file_name,
            mime_type=mime_type,
            uri=uri,
            owner=owner,
            conversation_id=conversation_id,
            last_updated=datetime.now(),
            active=True
        )
        self.session.add(item)
        self.session.commit()
        return item

    def update_item(self, item: Item, **kwargs) -> Optional[Item]:
        """Update an item's attributes"""
        for key, value in kwargs.items():
            if hasattr(item, key):
                setattr(item, key, value)
                
        item.last_updated = datetime.now()
        self.session.commit()
        return item

    def delete_item(self, owner: str, item_id: str) -> bool:
        """Delete an item (or mark as inactive)"""
        item = self.get_item_by_id(owner, item_id)
        if not item:
            return False
            
        # Soft delete - just mark as inactive
        item.active = False
        item.last_updated = datetime.now()
        self.session.commit()
        return True

    def hard_delete_item(self, owner: str, item_id: str) -> bool:
        """Permanently delete an item"""
        item = self.get_item_by_id(owner, item_id)
        if not item:
            return False
            
        self.session.delete(item)
        self.session.commit()
        return True

    def delete_conversation_items(self, conversation: Conversation, owner: User, permanent: bool = False) -> dict:
        """
        Delete all items in a conversation
        
        Args:
            conversation (Conversation): The conversation whose items should be deleted
            owner (User): The owner of the items
            permanent (bool): If True, permanently delete items. If False, soft delete
            
        Returns:
            dict: Summary of the operation
        """
        # Query items that belong to both the conversation and owner
        query = self.session.query(Item).filter(
            Item.conversation_id == conversation.id,
            Item.owner_id == owner.id
        )
        
        items = query.all()
        if not items:
            return {"message": "No items found", "deleted_count": 0}
            
        count = 0
        for item in items:
            if permanent:
                self.session.delete(item)
            else:
                item.active = False
                item.last_updated = datetime.now()
            count += 1
            
        self.session.commit()
        
        action = "permanently deleted" if permanent else "deactivated"
        return {
            "message": f"Successfully {action} {count} items",
            "deleted_count": count
        } 