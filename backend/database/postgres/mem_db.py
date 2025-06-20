# backend/database/postgres/mem_db.py
from typing import List, Dict, Optional
from .memories import get_memories, create_memory, update_memory, delete_memory, get_memory, search_memories
from .client import db_session_manager
from .models import Memory as MemoryModel
from sqlalchemy.orm import Session

def get_memories_db(uid: str, limit: int = 100, offset: int = 0) -> List[Dict]:
    return get_memories(uid, limit, offset)

def create_memory_db(uid: str, data: dict) -> Dict:
    return create_memory(uid, data)

def update_memory_db(uid: str, memory_id: str, data: dict) -> bool:
    return update_memory(uid, memory_id, data)

def delete_memory_db(uid: str, memory_id: str) -> bool:
    return delete_memory(uid, memory_id)

def get_memory_db(uid: str, memory_id: str) -> Optional[Dict]:
    return get_memory(uid, memory_id)

@db_session_manager
def get_memory_by_conversation_id(db: Session, conversation_id: str) -> Optional[Dict]:
    memory = db.query(MemoryModel).filter(MemoryModel.conversation_id == conversation_id).first()
    if memory:
        return {c.name: getattr(memory, c.name) for c in memory.__table__.columns}
    return None

def search_memories_by_text(uid: str, query: str, limit: int = 50) -> List[Dict]:
    return search_memories(uid, query, limit)