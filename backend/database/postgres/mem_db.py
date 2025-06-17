# backend/database/postgres/mem_db.py
# Memory database operations for PostgreSQL
# This provides the same interface as the firestore version

from datetime import datetime
from typing import List, Dict, Optional
from .memories import get_memories, create_memory, update_memory, delete_memory, get_memory


# Re-export memory functions with the same names as the firestore version
def get_memories_db(uid: str, limit: int = 100, offset: int = 0):
    """Get memories for a user"""
    return get_memories(uid, limit, offset)


def create_memory_db(uid: str, data: dict):
    """Create a new memory"""
    return create_memory(uid, data)


def update_memory_db(memory_id: str, data: dict):
    """Update a memory"""
    return update_memory(memory_id, data)


def delete_memory_db(memory_id: str):
    """Delete a memory"""
    return delete_memory(memory_id)


def get_memory_db(memory_id: str):
    """Get a specific memory"""
    return get_memory(memory_id)


# Additional functions that might be needed
def get_memory_by_conversation_id(conversation_id: str):
    """Get memory associated with a conversation"""
    from .client import get_db_session
    from .models import Memory as MemoryModel
    
    db = get_db_session()
    try:
        memory = db.query(MemoryModel).filter(MemoryModel.conversation_id == conversation_id).first()
        if memory:
            return {c.name: getattr(memory, c.name) for c in memory.__table__.columns}
        return None
    finally:
        db.close()


def search_memories_by_text(uid: str, query: str, limit: int = 50):
    """Search memories by text content"""
    from .memories import search_memories
    return search_memories(uid, query, limit)
