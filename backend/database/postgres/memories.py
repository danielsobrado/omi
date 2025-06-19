# backend/database/postgres/memories.py
import copy
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import desc, and_, or_

from database.helpers import prepare_for_write, prepare_for_read
from utils import encryption
from .client import get_db_session
from .models import Memory as MemoryModel

# *********************************
# ******* ENCRYPTION HELPERS ******
# *********************************

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

# *****************************
# ********** CRUD *************
# *****************************

@prepare_for_write(data_arg_name='data', prepare_func=_prepare_data_for_write)
def create_memory(uid: str, data: dict):
    db = get_db_session()
    try:
        memory = MemoryModel(uid=uid, **data)
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return {c.name: getattr(memory, c.name) for c in memory.__table__.columns}
    finally:
        db.close()

@prepare_for_read(decrypt_func=_prepare_memory_for_read)
def get_memory(uid: str, memory_id: str):
    db = get_db_session()
    try:
        memory = db.query(MemoryModel).filter(and_(MemoryModel.id == memory_id, MemoryModel.uid == uid)).first()
        if memory:
            return {c.name: getattr(memory, c.name) for c in memory.__table__.columns}
        return None
    finally:
        db.close()

@prepare_for_read(decrypt_func=_prepare_memory_for_read)
def get_memories(uid: str, limit: int = 100, offset: int = 0, categories: List[str] = []):
    db = get_db_session()
    try:
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
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [{c.name: getattr(mem, c.name) for c in mem.__table__.columns} for mem in memories]
    finally:
        db.close()

@prepare_for_write(data_arg_name='data', prepare_func=_prepare_data_for_write)
def update_memory(uid: str, memory_id: str, data: dict):
    db = get_db_session()
    try:
        memory = db.query(MemoryModel).filter(and_(MemoryModel.id == memory_id, MemoryModel.uid == uid)).first()
        if memory:
            for key, value in data.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()

def delete_memory(uid: str, memory_id: str):
    return update_memory(uid, memory_id, {'deleted': True})

def review_memory(uid: str, memory_id: str, value: bool):
    return update_memory(uid, memory_id, {'reviewed': True, 'user_review': value})

def change_memory_visibility(uid: str, memory_id: str, value: str):
    return update_memory(uid, memory_id, {'visibility': value})

def edit_memory(uid: str, memory_id: str, value: str):
    update_data = {'content': value, 'edited': True, 'updated_at': datetime.now(timezone.utc)}
    return update_memory(uid, memory_id, update_data)

def delete_all_memories(uid: str):
    db = get_db_session()
    try:
        db.query(MemoryModel).filter(MemoryModel.uid == uid).delete()
        db.commit()
    finally:
        db.close()

def delete_memories_for_conversation(uid: str, conversation_id: str):
    db = get_db_session()
    try:
        deleted_count = db.query(MemoryModel).filter(
            and_(MemoryModel.uid == uid, MemoryModel.conversation_id == conversation_id)
        ).delete()
        db.commit()
        return deleted_count
    finally:
        db.close()

def get_memory_count(uid: str):
    db = get_db_session()
    try:
        count = db.query(MemoryModel).filter(
            and_(MemoryModel.uid == uid, MemoryModel.discarded == False, MemoryModel.deleted == False)
        ).count()
        return count
    finally:
        db.close()

@prepare_for_read(decrypt_func=_prepare_memory_for_read)
def search_memories(uid: str, query: str, limit: int = 50):
    db = get_db_session()
    try:
        memories = (
            db.query(MemoryModel)
            .filter(
                and_(
                    MemoryModel.uid == uid,
                    MemoryModel.discarded == False,
                    MemoryModel.deleted == False,
                    or_(
                        MemoryModel.title.ilike(f"%{query}%"),
                        MemoryModel.overview.ilike(f"%{query}%")
                    )
                )
            )
            .order_by(desc(MemoryModel.created_at))
            .limit(limit)
            .all()
        )
        return [{c.name: getattr(mem, c.name) for c in mem.__table__.columns} for mem in memories]
    finally:
        db.close()

@prepare_for_read(decrypt_func=_prepare_memory_for_read)
def get_user_public_memories(uid: str, limit: int = 100, offset: int = 0):
    db = get_db_session()
    try:
        memories = (
            db.query(MemoryModel)
            .filter(
                and_(
                    MemoryModel.uid == uid,
                    MemoryModel.discarded == False,
                    MemoryModel.deleted == False,
                    or_(MemoryModel.visibility == 'public', MemoryModel.visibility.is_(None))
                )
            )
            .order_by(desc(MemoryModel.scoring), desc(MemoryModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [{c.name: getattr(mem, c.name) for c in mem.__table__.columns} for mem in memories]
    finally:
        db.close()