# backend/database/postgres/memories.py
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, and_, or_
from .client import get_db_session
from .models import Memory as MemoryModel


def create_memory(uid: str, data: dict):
    """Create a new memory"""
    db = get_db_session()
    try:
        memory = MemoryModel(uid=uid, **data)
        db.add(memory)
        db.commit()
        db.refresh(memory)
        return {c.name: getattr(memory, c.name) for c in memory.__table__.columns}
    finally:
        db.close()


def get_memory(memory_id: str):
    """Get memory by ID"""
    db = get_db_session()
    try:
        memory = db.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
        if memory:
            return {c.name: getattr(memory, c.name) for c in memory.__table__.columns}
        return None
    finally:
        db.close()


def get_memories(uid: str, limit: int = 100, offset: int = 0, categories: List[str] = []):
    """Get memories for a user"""
    print('get_memories db', uid, limit, offset, categories)
    
    db = get_db_session()
    try:
        query = db.query(MemoryModel).filter(and_(
            MemoryModel.uid == uid, 
            MemoryModel.discarded == False,
            MemoryModel.deleted == False
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


def update_memory(memory_id: str, data: dict):
    """Update memory"""
    db = get_db_session()
    try:
        memory = db.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
        if memory:
            for key, value in data.items():
                if hasattr(memory, key):
                    setattr(memory, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()


def delete_memory(memory_id: str):
    """Mark memory as deleted"""
    db = get_db_session()
    try:
        memory = db.query(MemoryModel).filter(MemoryModel.id == memory_id).first()
        if memory:
            memory.deleted = True
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_memory_count(uid: str):
    """Get total memory count for user"""
    db = get_db_session()
    try:
        count = db.query(MemoryModel).filter(
            and_(
                MemoryModel.uid == uid, 
                MemoryModel.discarded == False,
                MemoryModel.deleted == False
            )
        ).count()
        return count
    finally:
        db.close()


def search_memories(uid: str, query: str, limit: int = 50):
    """Search memories by title or overview"""
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


def get_user_public_memories(uid: str, limit: int = 100, offset: int = 0):
    """Get public memories for a user"""
    print('get_public_memories', limit, offset)
    
    db = get_db_session()
    try:
        memories = (
            db.query(MemoryModel)
            .filter(
                and_(
                    MemoryModel.uid == uid,
                    MemoryModel.discarded == False,
                    MemoryModel.deleted == False,
                    or_(MemoryModel.visibility == 'public', MemoryModel.visibility.is_(None))  # Default to public if not set
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
