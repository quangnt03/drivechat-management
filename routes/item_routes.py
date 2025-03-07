from fastapi import APIRouter, Depends, HTTPException, Query
from services.db import DatabaseService
from services.item_service import ItemService
from dependencies.security import validate_token
from typing import Optional
from pydantic import BaseModel
import os

item_router = APIRouter()

# Dependency to get database session
def get_item_service():
    db = DatabaseService(os.getenv("DATABASE_URL"))
    try:
        service = ItemService(db.session)
        yield service
    finally:
        db.session.close()

# Pydantic models for request/response validation
class ItemCreate(BaseModel):
    file_name: str
    mime_type: str
    uri: str
    conversation_id: str

class ItemUpdate(BaseModel):
    file_name: Optional[str] = None
    active: Optional[bool] = None

@item_router.get("/")
def get_items(
    search: Optional[str] = None,
    mime_type: Optional[str] = None,
    active_only: bool = False,
    current_user: dict = Depends(validate_token),
    item_service: ItemService = Depends(get_item_service)
):
    """
    Get items with optional filters
    
    Args:
        search (str, optional): Search term for file names
        mime_type (str, optional): Filter by mime type
        active_only (bool): If True, return only active items. If False, return all items
    """
    owner = current_user["UserAttributes"][0]["Value"]
    if search:
        return item_service.search_items(
            search_term=search, 
            owner=owner, 
            mime_type=mime_type, 
            active_only=active_only
        )
    return item_service.get_items_by_owner(owner, active_only)

@item_router.get("/recent")
def get_recent_items(
    limit: int = Query(10, gt=0, le=100),
    current_user: dict = Depends(validate_token),
    item_service: ItemService = Depends(get_item_service)
):
    """Get recently updated items"""
    owner = current_user["UserAttributes"][0]["Value"]
    return item_service.get_recent_items(limit, owner)

@item_router.get("/{item_id}")
def get_item(
    item_id: str,
    current_user: dict = Depends(validate_token),
    item_service: ItemService = Depends(get_item_service)
):
    """Get a specific item by ID"""
    owner = current_user["UserAttributes"][0]["Value"]
    item = item_service.get_item_by_id(owner, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@item_router.post("/")
def create_item(
    item_data: ItemCreate,
    current_user: dict = Depends(validate_token),
    item_service: ItemService = Depends(get_item_service)
):
    """Create a new item"""
    owner = current_user["UserAttributes"][0]["Value"]
    return item_service.create_item(
        file_name=item_data.file_name,
        mime_type=item_data.mime_type,
        uri=item_data.uri,
        owner=owner,
        conversation_id=item_data.conversation_id
    )

@item_router.put("/{item_id}")
def update_item(
    item_id: str,
    item_data: ItemUpdate,
    current_user: dict = Depends(validate_token),
    item_service: ItemService = Depends(get_item_service)
):
    """Update an item"""
    owner = current_user["UserAttributes"][0]["Value"]
    item = item_service.get_item_by_id(owner, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    update_data = item_data.dict(exclude_unset=True)
    updated_item = item_service.update_item(owner, item_id, **update_data)
    return updated_item

@item_router.delete("/{item_id}")
def delete_item(
    item_id: str,
    permanent: bool = False,
    current_user: dict = Depends(validate_token),
    item_service: ItemService = Depends(get_item_service)
):
    """Delete an item (soft delete by default)"""
    owner = current_user["UserAttributes"][0]["Value"]
    item = item_service.get_item_by_id(owner, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
        
    if permanent:
        success = item_service.hard_delete_item(owner, item_id)
    else:
        success = item_service.delete_item(owner, item_id)
        
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted successfully"}
