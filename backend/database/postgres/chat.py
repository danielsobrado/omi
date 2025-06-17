# backend/database/postgres/chat.py
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import desc, and_
import uuid
from .client import get_db_session
from .models import Message as MessageModel, Conversation as ConversationModel
from models.chat import Message


def save_message(uid: str, message_data: dict):
    """Save a chat message"""
    db = get_db_session()
    try:
        # Filter dictionary to only include columns present in the SQLAlchemy model
        model_columns = {c.name for c in MessageModel.__table__.columns}
        filtered_data = {k: v for k, v in message_data.items() if k in model_columns}

        message = MessageModel(uid=uid, **filtered_data)
        db.add(message)
        db.commit()
        db.refresh(message)
        return {c.name: getattr(message, c.name) for c in message.__table__.columns}
    finally:
        db.close()


def add_message(uid: str, message_data: dict):
    """Add a message - alias for save_message to match Firestore API"""
    return save_message(uid, message_data)


def get_messages(uid: str, session_id: str = None, limit: int = 100):
    """Get chat messages for a user/session"""
    db = get_db_session()
    try:
        query = db.query(MessageModel).filter(MessageModel.uid == uid)
        
        if session_id:
            query = query.filter(MessageModel.session_id == session_id)
            
        messages = (
            query.order_by(desc(MessageModel.created_at))
            .limit(limit)
            .all()
        )
        return [{c.name: getattr(msg, c.name) for c in msg.__table__.columns} for msg in messages]
    finally:
        db.close()


def get_message(message_id: str):
    """Get a specific message"""
    db = get_db_session()
    try:
        message = db.query(MessageModel).filter(MessageModel.id == message_id).first()
        if message:
            return {c.name: getattr(message, c.name) for c in message.__table__.columns}
        return None
    finally:
        db.close()


def delete_message(message_id: str):
    """Delete a message"""
    db = get_db_session()
    try:
        message = db.query(MessageModel).filter(MessageModel.id == message_id).first()
        if message:
            db.delete(message)
            db.commit()
            return True
        return False
    finally:
        db.close()


def clear_session_messages(uid: str, session_id: str):
    """Clear all messages for a session"""
    db = get_db_session()
    try:
        messages = db.query(MessageModel).filter(
            and_(MessageModel.uid == uid, MessageModel.session_id == session_id)
        ).all()
        
        for message in messages:
            db.delete(message)
        
        db.commit()
        return len(messages)
    finally:
        db.close()


def get_sessions(uid: str):
    """Get all session IDs for a user"""
    db = get_db_session()
    try:
        sessions = (
            db.query(MessageModel.session_id)
            .filter(MessageModel.uid == uid)
            .distinct()
            .all()
        )
        return [session[0] for session in sessions if session[0]]
    finally:
        db.close()


def add_app_message(text: str, app_id: str, uid: str, conversation_id: Optional[str] = None) -> Message:
    """Add an app message"""
    ai_message = Message(
        id=str(uuid.uuid4()),
        text=text,
        created_at=datetime.now(timezone.utc),
        sender='ai',
        app_id=app_id,
        from_external_integration=False,
        type='text',
        memories_id=[conversation_id] if conversation_id else [],
    )
    
    # Save to database
    message_data = ai_message.model_dump()
    save_message(uid, message_data)
    return ai_message


def get_app_messages(uid: str, app_id: str, limit: int = 20, offset: int = 0, include_conversations: bool = False):
    """Get messages for a specific app"""
    db = get_db_session()
    try:
        query = (
            db.query(MessageModel)
            .filter(and_(
                MessageModel.uid == uid,
                MessageModel.app_id == app_id
            ))
            .order_by(desc(MessageModel.created_at))
            .limit(limit)
            .offset(offset)
        )
        
        messages = query.all()
        result = [{c.name: getattr(msg, c.name) for c in msg.__table__.columns} for msg in messages]
        
        if include_conversations:
            # TODO: Add conversation details if needed
            pass
            
        return result
    finally:
        db.close()