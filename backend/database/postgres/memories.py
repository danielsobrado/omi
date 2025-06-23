# backend/database/postgres/memories.py
import copy
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import desc, and_, or_, func
from sqlalchemy.orm import Session

from database.helpers import prepare_for_write, prepare_for_read, set_data_protection_level
from utils import encryption
from .client import db_session_manager
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

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_memory_for_read)
def get_memories(db: Session, uid: str, limit: int = 100, offset: int = 0, categories: List[str] = []):
    logging.info(f'get_memories db {uid} {limit} {offset} {categories}')
    
    query = db.query(MemoryModel).filter(
        and_(
            MemoryModel.uid == uid,
            or_(MemoryModel.deleted == False, MemoryModel.deleted.is_(None)),
            or_(MemoryModel.discarded == False, MemoryModel.discarded.is_(None))
        )
    )
    
    if categories:
        query = query.filter(MemoryModel.category.in_(categories))
    
    memories = (
        query.order_by(desc(MemoryModel.scoring), desc(MemoryModel.created_at))
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    # Convert to dict and filter by user_review
    memories_data = [{c.name: getattr(mem, c.name) for c in mem.__table__.columns} for mem in memories]
    logging.info(f"get_memories found {len(memories_data)} memories")
    
    # Filter out memories with user_review = False
    result = [memory for memory in memories_data if memory.get('user_review') is not False]
    return result

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_memory_for_read)
def get_user_public_memories(db: Session, uid: str, limit: int = 100, offset: int = 0):
    logging.info(f'get_public_memories {limit} {offset}')

    memories = db.query(MemoryModel).filter(
        and_(
            MemoryModel.uid == uid,
            or_(MemoryModel.deleted == False, MemoryModel.deleted.is_(None)),
            or_(MemoryModel.discarded == False, MemoryModel.discarded.is_(None))
        )
    ).order_by(desc(MemoryModel.scoring), desc(MemoryModel.created_at)).limit(limit).offset(offset).all()

    memories_data = [{c.name: getattr(mem, c.name) for c in mem.__table__.columns} for mem in memories]

    # Consider visibility as 'public' if it's missing
    public_memories = [memory for memory in memories_data if memory.get('visibility', 'public') == 'public']
    return public_memories

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_memory_for_read)
def get_non_filtered_memories(db: Session, uid: str, limit: int = 100, offset: int = 0):
    logging.info(f'get_non_filtered_memories {uid} {limit} {offset}')
    
    memories = db.query(MemoryModel).filter(
        and_(
            MemoryModel.uid == uid,
            or_(MemoryModel.deleted == False, MemoryModel.deleted.is_(None))
        )
    ).order_by(desc(MemoryModel.created_at)).limit(limit).offset(offset).all()
    
    return [{c.name: getattr(mem, c.name) for c in mem.__table__.columns} for mem in memories]

@db_session_manager
@set_data_protection_level(data_arg_name='data')
@prepare_for_write(data_arg_name='data', prepare_func=_prepare_data_for_write)
def create_memory(db: Session, uid: str, data: dict):
    model_columns = {c.name for c in MemoryModel.__table__.columns}
    filtered_data = {k: v for k, v in data.items() if k in model_columns}
    
    memory = MemoryModel(uid=uid, **filtered_data)
    db.add(memory)
    db.flush()

@db_session_manager
@set_data_protection_level(data_arg_name='data')
@prepare_for_write(data_arg_name='data', prepare_func=_prepare_data_for_write)
def save_memories(db: Session, uid: str, data: List[dict]):
    if not data:
        return

    model_columns = {c.name for c in MemoryModel.__table__.columns}
    
    for memory_data in data:
        filtered_data = {k: v for k, v in memory_data.items() if k in model_columns}
        
        # Check if memory exists
        existing = db.query(MemoryModel).filter(
            and_(MemoryModel.uid == uid, MemoryModel.id == filtered_data['id'])
        ).first()
        
        if existing:
            # Update existing
            for key, value in filtered_data.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
        else:
            # Create new
            memory = MemoryModel(uid=uid, **filtered_data)
            db.add(memory)
    
    db.flush()

@db_session_manager
def delete_memories(db: Session, uid: str):
    """Soft delete all memories for a user"""
    db.query(MemoryModel).filter(MemoryModel.uid == uid).update({
        'deleted': True,
        'updated_at': datetime.now(timezone.utc)
    })
    db.commit()

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_memory_for_read)
def get_memory(db: Session, uid: str, memory_id: str):
    memory = db.query(MemoryModel).filter(
        and_(
            MemoryModel.uid == uid,
            MemoryModel.id == memory_id,
            or_(MemoryModel.deleted == False, MemoryModel.deleted.is_(None))
        )
    ).first()
    
    if memory:
        return {c.name: getattr(memory, c.name) for c in memory.__table__.columns}
    return None

@db_session_manager
def review_memory(db: Session, uid: str, memory_id: str, value: bool):
    memory = db.query(MemoryModel).filter(
        and_(MemoryModel.uid == uid, MemoryModel.id == memory_id)
    ).first()
    
    if memory:
        memory.reviewed = True
        memory.user_review = value
        memory.updated_at = datetime.now(timezone.utc)
        db.commit()

@db_session_manager
def change_memory_visibility(db: Session, uid: str, memory_id: str, value: str):
    memory = db.query(MemoryModel).filter(
        and_(MemoryModel.uid == uid, MemoryModel.id == memory_id)
    ).first()
    
    if memory:
        memory.visibility = value
        memory.updated_at = datetime.now(timezone.utc)
        db.commit()

@db_session_manager
def edit_memory(db: Session, uid: str, memory_id: str, value: str):
    memory = db.query(MemoryModel).filter(
        and_(MemoryModel.uid == uid, MemoryModel.id == memory_id)
    ).first()
    
    if not memory:
        return

    # Handle encryption based on current protection level
    doc_level = getattr(memory, 'data_protection_level', 'standard')
    content = value
    if doc_level == 'enhanced':
        content = encryption.encrypt(content, uid)

    memory.content = content
    memory.edited = True
    memory.updated_at = datetime.now(timezone.utc)
    db.commit()

@db_session_manager
def delete_memory(db: Session, uid: str, memory_id: str):
    """Soft delete a specific memory"""
    memory = db.query(MemoryModel).filter(
        and_(MemoryModel.uid == uid, MemoryModel.id == memory_id)
    ).first()
    
    if memory:
        memory.deleted = True
        memory.updated_at = datetime.now(timezone.utc)
        db.commit()

@db_session_manager
def delete_all_memories(db: Session, uid: str):
    """Hard delete all memories for a user"""
    db.query(MemoryModel).filter(MemoryModel.uid == uid).delete()
    db.commit()

@db_session_manager
def delete_memories_for_conversation(db: Session, uid: str, memory_id: str):
    """Delete memories related to a specific conversation/memory_id"""
    deleted_count = db.query(MemoryModel).filter(
        and_(
            MemoryModel.uid == uid,
            MemoryModel.memory_id == memory_id
        )
    ).delete(synchronize_session=False)
    
    db.commit()
    logging.info(f'delete_memories_for_conversation {memory_id} {deleted_count}')
    
@db_session_manager
@set_data_protection_level(data_arg_name='data')
@prepare_for_write(data_arg_name='data', prepare_func=_prepare_data_for_write)
def update_memory(db: Session, uid: str, memory_id: str, data: dict) -> bool:
    """Update an existing memory with new data."""
    memory = db.query(MemoryModel).filter(
        and_(MemoryModel.uid == uid, MemoryModel.id == memory_id)
    ).first()
    
    if memory:
        for key, value in data.items():
            if hasattr(memory, key):
                setattr(memory, key, value)
        
        memory.updated_at = datetime.now(timezone.utc)
        db.flush()
        return True
    return False

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_memory_for_read)
def search_memories(db: Session, uid: str, query: str, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Search memories by text content. This is a basic implementation using PostgreSQL's
    text search. For production, you might want to use a more sophisticated search engine.
    """
    # Basic text search using PostgreSQL's ILIKE for partial matching
    # For better search, consider using PostgreSQL's full-text search or a dedicated search engine
    memories = db.query(MemoryModel).filter(
        and_(
            MemoryModel.uid == uid,
            or_(MemoryModel.deleted == False, MemoryModel.deleted.is_(None)),
            or_(MemoryModel.discarded == False, MemoryModel.discarded.is_(None)),
            or_(
                MemoryModel.content.ilike(f'%{query}%'),
                MemoryModel.title.ilike(f'%{query}%'),
                MemoryModel.overview.ilike(f'%{query}%')
            )
        )
    ).order_by(desc(MemoryModel.scoring), desc(MemoryModel.created_at)).limit(limit).offset(offset).all()
    
    return [{c.name: getattr(mem, c.name) for c in mem.__table__.columns} for mem in memories]

# **************************************
# ********* MIGRATION HELPERS **********
# **************************************

@db_session_manager
def get_memories_to_migrate(db: Session, uid: str, target_level: str) -> List[dict]:
    """
    Finds all memories that are not at the target protection level.
    """
    memories = db.query(MemoryModel).filter(
        and_(
            MemoryModel.uid == uid,
            or_(
                MemoryModel.data_protection_level != target_level,
                MemoryModel.data_protection_level.is_(None)
            )
        )
    ).all()

    return [{'id': str(mem.id), 'type': 'memory'} for mem in memories]

@db_session_manager
def migrate_memories_level_batch(db: Session, uid: str, memory_ids: List[str], target_level: str):
    """
    Migrates a batch of memories to the target protection level.
    """
    try:
        memories = db.query(MemoryModel).filter(
            and_(
                MemoryModel.uid == uid,
                MemoryModel.id.in_(memory_ids)
            )
        ).all()

        for memory in memories:
            current_level = getattr(memory, 'data_protection_level', 'standard')
            
            if current_level == target_level:
                continue

            # Convert to dict for processing
            memory_data = {c.name: getattr(memory, c.name) for c in memory.__table__.columns}
            plain_data = _prepare_memory_for_read(memory_data, uid)
            plain_content = plain_data.get('content')
            
            migrated_content = plain_content
            if target_level == 'enhanced' and isinstance(plain_content, str):
                migrated_content = encryption.encrypt(plain_content, uid)

            memory.data_protection_level = target_level
            memory.content = migrated_content
            memory.updated_at = datetime.now(timezone.utc)

        db.commit()
        logging.info(f"Successfully migrated {len(memories)} memories to {target_level} level")
        
    except Exception as e:
        db.rollback()
        logging.error(f"Migration failed: {e}")
        raise

@db_session_manager
def migrate_memories(db: Session, prev_uid: str, new_uid: str, app_id: str = None):
    """
    Migrate memories from one user to another.
    If app_id is provided, only migrate memories related to that app.
    """
    logging.info(f'Migrating memories from {prev_uid} to {new_uid}')

    # Build query for source memories
    query = db.query(MemoryModel).filter(MemoryModel.uid == prev_uid)
    
    if app_id:
        query = query.filter(MemoryModel.app_id == app_id)

    memories_to_migrate = query.all()

    if not memories_to_migrate:
        logging.info(f'No memories to migrate for user {prev_uid}')
        return 0

    # Create new memory records for destination user
    migrated_count = 0
    for old_memory in memories_to_migrate:
        memory_data = {c.name: getattr(old_memory, c.name) for c in old_memory.__table__.columns}
        
        # Update uid and create new memory
        memory_data['uid'] = new_uid
        new_memory = MemoryModel(**memory_data)
        db.add(new_memory)
        migrated_count += 1

    db.commit()
    logging.info(f'Migrated {migrated_count} memories from {prev_uid} to {new_uid}')
    return migrated_count