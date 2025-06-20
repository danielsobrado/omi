# backend/database/postgres/memories.py
import copy
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import Session

from database.helpers import prepare_for_write, prepare_for_read
from utils import encryption
from .client import db_session_manager
from .models import Memory as MemoryModel

# --- ENCRYPTION HELPERS (same as before) ---
def _encrypt_memory_data(memory_data: Dict[str, Any], uid: str) -> Dict[str, Any]:
    data = copy.deepcopy(memory_data)
    if 'content' in data and isinstance(data['content'], str):
        data['content'] = encryption.encrypt(data['content'], uid)
    return data

def _decrypt_memory_data(memory_data: Dict[str, Any], uid: str) -> Dict[str, Any]:
    data = copy.deepcopy(memory_data)
    if 'content' in data and isinstance(data['content'], str):
        try:
            data['content'] = encryption.decrypt(data['content'], uid)
        except Exception:
            pass
    return data

def _prepare_data_for_write(data: Dict[str, Any], uid: str, level: str) -> Dict[str, Any]:
    if level == 'enhanced':
        return _encrypt_memory_data(data, uid)
    return data

def _prepare_memory_for_read(memory_data: Optional[Dict[str, Any]], uid: str) -> Optional[Dict[str, Any]]:
    if not memory_data:
        return None
    level = memory_data.get('data_protection_level')
    if level == 'enhanced':
        return _decrypt_memory_data(memory_data, uid)
    return memory_data
# --- END ENCRYPTION HELPERS ---

@db_session_manager
@prepare_for_write(data_arg_name='data', prepare_func=_prepare_data_for_write)
def create_memory(db: Session, uid: str, data: dict) -> Dict[str, Any]:
    memory = MemoryModel(uid=uid, **data)
    db.add(memory)
    db.flush()
    return {c.name: getattr(memory, c.name) for c in memory.__table__.columns}

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_memory_for_read)
def get_memory(db: Session, uid: str, memory_id: str) -> Optional[Dict[str, Any]]:
    memory = db.query(MemoryModel).filter(and_(MemoryModel.id == memory_id, MemoryModel.uid == uid)).first()
    if memory:
        return {c.name: getattr(memory, c.name) for c in memory.__table__.columns}
    return None

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_memory_for_read)
def get_memories(db: Session, uid: str, limit: int = 100, offset: int = 0, categories: List[str] = []) -> List[Dict[str, Any]]:
    query = db.query(MemoryModel).filter(and_(
        MemoryModel.uid == uid,
        MemoryModel.discarded == False,
        MemoryModel.deleted == False,
        MemoryModel.user_review != False
    ))
    if categories:
        query = query.filter(MemoryModel.category.in_(categories))
    memories = (
        query
        .order_by(desc(MemoryModel.scoring), desc(MemoryModel.created_at))
        .limit(limit).offset(offset).all()
    )
    return [{c.name: getattr(mem, c.name) for c in mem.__table__.columns} for mem in memories]

@db_session_manager
@prepare_for_write(data_arg_name='data', prepare_func=_prepare_data_for_write)
def update_memory(db: Session, uid: str, memory_id: str, data: dict) -> bool:
    memory = db.query(MemoryModel).filter(and_(MemoryModel.id == memory_id, MemoryModel.uid == uid)).first()
    if memory:
        for key, value in data.items():
            if hasattr(memory, key):
                setattr(memory, key, value)
        return True
    return False

def delete_memory(uid: str, memory_id: str) -> bool:
    return update_memory(uid, memory_id, {'deleted': True})

def review_memory(uid: str, memory_id: str, value: bool) -> bool:
    return update_memory(uid, memory_id, {'reviewed': True, 'user_review': value})

def edit_memory(uid: str, memory_id: str, value: str) -> bool:
    update_data = {'content': value, 'edited': True, 'updated_at': datetime.now(timezone.utc)}
    return update_memory(uid, memory_id, update_data)

@db_session_manager
def delete_memories_for_conversation(db: Session, uid: str, conversation_id: str) -> int:
    deleted_count = db.query(MemoryModel).filter(
        and_(MemoryModel.uid == uid, MemoryModel.conversation_id == conversation_id)
    ).delete(synchronize_session=False)
    logging.info(f"Deleted {deleted_count} memories for conversation {conversation_id}")
    return deleted_count