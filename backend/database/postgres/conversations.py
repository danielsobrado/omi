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


def get_conversation(conversation_id: str):
    """Get conversation by ID"""
    db = get_db_session()
    try:
        conversation = db.query(ConversationModel).filter(ConversationModel.id == conversation_id).first()
        if conversation:
            return {c.name: getattr(conversation, c.name) for c in conversation.__table__.columns}
        return None
    finally:
        db.close()


def get_conversations(uid: str, limit: int = 100, offset: int = 0):
    """Get conversations for a user"""
    db = get_db_session()
    try:
        conversations = (
            db.query(ConversationModel)
            .filter(and_(ConversationModel.uid == uid, ConversationModel.discarded == False))
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
