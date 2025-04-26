from fastapi import APIRouter, Depends, HTTPException
from dependencies.database import DatabaseService, UserService, ItemService, ConversationService
from dependencies.security import validate_token
from typing import Optional
from pydantic import BaseModel, UUID4
import os
from models.conversation import Conversation
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

item_router = APIRouter()
db_service = DatabaseService(os.getenv("DATABASE_URL"))


# Pydantic models for request/response validation
class ItemCreate(BaseModel):
    file_name: str
    mime_type: str
    uri: str
    conversation_id: str

class ItemUpdate(BaseModel):
    file_name: Optional[str] = None
    active: Optional[bool] = None

@item_router.get("")
def get_items(
    search: Optional[str] = None,
    mime_type: Optional[str] = None,
    conversation_id: Optional[UUID4] = None,
    active_only: bool = False,
    current_user: dict = Depends(validate_token),
    item_service: ItemService = Depends(db_service.get_item_service),
    user_service: UserService = Depends(db_service.get_user_service),
    conversation_service: ConversationService = Depends(db_service.get_conversation_service)
):
    """
    Get items with optional filters
    
    Args:
        search (str, optional): Search term for file names
        mime_type (str, optional): Filter by mime type
        active_only (bool): If True, return only active items. If False, return all items
    """
    owner = current_user["UserAttributes"][0]["Value"]
    user = user_service.get_user_by_email(owner)
    if not user:
        user = user_service.create_user(owner)
    if search:
        return item_service.search_items(
            search_term=search, 
            owner=user, 
            mime_type=mime_type, 
            active_only=active_only
        )
    if conversation_id:
        conversation = conversation_service.get_conversation(conversation_id, user.id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return item_service.get_items_by_conversation(conversation, active_only)
    return item_service.get_items_by_owner(user, active_only)


@item_router.get("/{item_id}")
def get_item(
    item_id: UUID4,
    current_user: dict = Depends(validate_token),
    item_service: ItemService = Depends(db_service.get_item_service),
    user_service: UserService = Depends(db_service.get_user_service)
):
    """Get a specific item by ID"""
    owner = current_user["UserAttributes"][0]["Value"]
    user = user_service.get_user_by_email(owner)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    item = item_service.get_item_by_id(user, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@item_router.put("/{item_id}")
def update_item(
    item_id: UUID4,
    item_data: ItemUpdate,
    current_user: dict = Depends(validate_token),
    item_service: ItemService = Depends(db_service.get_item_service),
    user_service: UserService = Depends(db_service.get_user_service)
):
    """Update an item"""
    owner = current_user["UserAttributes"][0]["Value"]
    user = user_service.get_user_by_email(owner)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    item = item_service.get_item_by_id(user, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    update_data = item_data.dict(exclude_unset=True)
    updated_item = item_service.update_item(item, **update_data)
    return updated_item


@item_router.delete("/{item_id}")
def delete_item(
    item_id: UUID4,
    permanent: bool = False,
    current_user: dict = Depends(validate_token),
    item_service: ItemService = Depends(db_service.get_item_service),
    user_service: UserService = Depends(db_service.get_user_service)
):
    """Delete an item (soft delete by default)"""
    owner = current_user["UserAttributes"][0]["Value"]
    user = user_service.get_user_by_email(owner)
    item = item_service.get_item_by_id(user, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    if permanent:
        success = item_service.hard_delete_item(user, item_id)
    else:
        success = item_service.delete_item(user, item_id)
        
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}


@item_router.delete("/conversation/{conversation_id}")
def delete_conversation_items(
    conversation_id: str,
    permanent: bool = False,
    current_user: dict = Depends(validate_token),
    item_service: ItemService = Depends(db_service.get_item_service),
    user_service: UserService = Depends(db_service.get_user_service)
):
    """
    Delete all items in a conversation
    
    Args:
        conversation_id (str): ID of the conversation
        permanent (bool): If True, permanently delete items. If False, soft delete (default)
    """
    owner = current_user["UserAttributes"][0]["Value"]
    user = user_service.get_user_by_email(owner)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Get conversation (you might need to adjust this based on your conversation model)
    conversation = item_service.session.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user.id
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    result = item_service.delete_conversation_items(
        conversation=conversation,
        owner=user,
        permanent=permanent
    )
    
    return result
