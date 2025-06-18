# backend/database/postgres/conversations.py
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, and_, or_
from .client import get_db_session
from .models import Conversation as ConversationModel


def create_conversation(uid: str, data: dict):
    """Create a new conversation"""
    db = get_db_session()
    try:
        conversation = ConversationModel(uid=uid, **data)
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return {c.name: getattr(conversation, c.name) for c in conversation.__table__.columns}
    finally:
        db.close()


def get_conversation(uid: str, conversation_id: str):
    """Get conversation by ID for a specific user"""
    db = get_db_session()
    try:
        conversation = db.query(ConversationModel).filter(
            ConversationModel.id == conversation_id,
            ConversationModel.uid == uid
        ).first()
        if conversation:
            return {c.name: getattr(conversation, c.name) for c in conversation.__table__.columns}
        return None
    finally:
        db.close()


def get_conversations(uid: str, limit: int = 100, offset: int = 0, include_discarded: bool = False,
                      statuses: List[str] = [], start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None, categories: Optional[List[str]] = None):
    """Get conversations for a user"""
    db = get_db_session()
    try:
        query = db.query(ConversationModel).filter(ConversationModel.uid == uid)
        
        # Filter by discarded status
        if not include_discarded:
            query = query.filter(ConversationModel.discarded == False)
            
        # Filter by statuses
        if statuses:
            query = query.filter(ConversationModel.status.in_(statuses))
            
        # Filter by date range
        if start_date:
            query = query.filter(ConversationModel.created_at >= start_date)
        if end_date:
            query = query.filter(ConversationModel.created_at <= end_date)
            
        # Note: categories filtering would need to be implemented based on your schema
        # For now, ignoring categories parameter as it's not clear how it's stored
        
        conversations = (
            query
            .order_by(desc(ConversationModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [{c.name: getattr(conv, c.name) for c in conv.__table__.columns} for conv in conversations]
    finally:
        db.close()


def update_conversation(conversation_id: str, data: dict):
    """Update conversation"""
    db = get_db_session()
    try:
        conversation = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
        if conversation:
            for key, value in data.items():
                if hasattr(conversation, key):
                    setattr(conversation, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()


def delete_conversation(conversation_id: str):
    """Mark conversation as discarded"""
    db = get_db_session()
    try:
        conversation = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
        if conversation:
            conversation.discarded = True
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_conversation_count(uid: str):
    """Get total conversation count for user"""
    db = get_db_session()
    try:
        count = db.query(ConversationModel).filter(
            and_(ConversationModel.uid == uid, ConversationModel.discarded == False)
        ).count()
        return count
    finally:
        db.close()


def search_conversations(uid: str, query: str, limit: int = 50):
    """Search conversations by title or overview"""
    db = get_db_session()
    try:
        conversations = (
            db.query(ConversationModel)
            .filter(
                and_(
                    ConversationModel.uid == uid,
                    ConversationModel.discarded == False,
                    or_(
                        ConversationModel.title.ilike(f"%{query}%"),
                        ConversationModel.overview.ilike(f"%{query}%")
                    )
                )
            )
            .order_by(desc(ConversationModel.created_at))
            .limit(limit)
            .all()
        )
        return [{c.name: getattr(conv, c.name) for c in conv.__table__.columns} for conv in conversations]
    finally:
        db.close()


def get_conversations_by_id(uid: str, conversation_ids):
    """Get conversations by list of IDs"""
    db = get_db_session()
    try:
        conversations = (
            db.query(ConversationModel)
            .filter(
                and_(
                    ConversationModel.uid == uid,
                    ConversationModel.id.in_(conversation_ids),
                    ConversationModel.discarded == False
                )
            )
            .all()
        )
        return [{c.name: getattr(conv, c.name) for c in conv.__table__.columns} for conv in conversations]
    finally:
        db.close()


def get_closest_conversation_to_timestamps(uid: str, start_timestamp: int, end_timestamp: int):
    """Get the closest conversation to given timestamps"""
    db = get_db_session()
    try:
        from datetime import datetime, timedelta
        
        start_threshold = datetime.utcfromtimestamp(start_timestamp) - timedelta(minutes=2)
        end_threshold = datetime.utcfromtimestamp(end_timestamp) + timedelta(minutes=2)
        
        conversations = (
            db.query(ConversationModel)
            .filter(
                and_(
                    ConversationModel.uid == uid,
                    ConversationModel.finished_at >= start_threshold,
                    ConversationModel.started_at <= end_threshold,
                    ConversationModel.discarded == False
                )
            )
            .order_by(desc(ConversationModel.created_at))
            .all()
        )
        
        if not conversations:
            return None
        
        # Find the conversation with the closest start or end timestamp
        closest_conversation = None
        min_diff = float('inf')
        
        for conversation in conversations:
            conversation_start_timestamp = conversation.started_at.timestamp() if conversation.started_at else start_timestamp
            conversation_end_timestamp = conversation.finished_at.timestamp() if conversation.finished_at else end_timestamp
            
            diff1 = abs(conversation_start_timestamp - start_timestamp)
            diff2 = abs(conversation_end_timestamp - end_timestamp)
            
            if diff1 < min_diff or diff2 < min_diff:
                min_diff = min(diff1, diff2)
                closest_conversation = conversation
        
        if closest_conversation:
            return {c.name: getattr(closest_conversation, c.name) for c in closest_conversation.__table__.columns}
        return None
    finally:
        db.close()


def update_conversation_segments(uid: str, conversation_id: str, segments: list):
    """Update conversation segments"""
    db = get_db_session()
    try:
        conversation = db.query(ConversationModel).filter(
            and_(
                ConversationModel.uid == uid,
                ConversationModel.id == conversation_id
            )
        ).first()
        
        if conversation:
            conversation.transcript_segments = segments
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_in_progress_conversation(uid: str):
    """Get conversation that is currently in progress"""
    db = get_db_session()
    try:
        conversation = (
            db.query(ConversationModel)
            .filter(
                and_(
                    ConversationModel.uid == uid,
                    ConversationModel.status == 'in_progress',
                    ConversationModel.discarded == False
                )
            )
            .first()
        )
        
        if conversation:
            return {c.name: getattr(conversation, c.name) for c in conversation.__table__.columns}
        return None
    finally:
        db.close()
