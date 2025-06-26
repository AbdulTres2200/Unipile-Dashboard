# backend/routes/messages.py

from fastapi import APIRouter, HTTPException
from services.supabase_service import supabase_service
from typing import List, Dict, Any

router = APIRouter()

@router.get("/people")
async def get_all_people():
    """Get all people with message counts and latest message info"""
    try:
        people = supabase_service.get_all_people_with_stats()
        return {"people": people, "total": len(people)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/people/{person_id}/messages")
async def get_person_messages(person_id: str):
    """Get all messages for a specific person"""
    try:
        messages = supabase_service.get_messages_by_person(person_id)
        return {"messages": messages, "total": len(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/messages")
async def get_recent_messages(limit: int = 50):
    """Get recent messages across all accounts"""
    try:
        messages = supabase_service.get_recent_messages(limit)
        return {"messages": messages, "total": len(messages)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats")
async def get_message_stats():
    """Get overall message statistics"""
    try:
        stats = supabase_service.get_message_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))