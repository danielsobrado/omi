# backend/database/postgres/trends.py
from datetime import datetime
from typing import List, Dict
from sqlalchemy import func, desc, and_
from .client import get_db_session
from .models import Memory as MemoryModel, Conversation as ConversationModel


def get_trends_data(uid: str, start_date: datetime = None, end_date: datetime = None):
    """Get trends data for a user"""
    db = get_db_session()
    try:
        # Memory trends by category
        memory_query = db.query(
            MemoryModel.category,
            func.count(MemoryModel.id).label('count')
        ).filter(
            and_(
                MemoryModel.uid == uid,
                MemoryModel.discarded == False,
                MemoryModel.deleted == False
            )
        )
        
        if start_date:
            memory_query = memory_query.filter(MemoryModel.created_at >= start_date)
        if end_date:
            memory_query = memory_query.filter(MemoryModel.created_at <= end_date)
            
        memory_trends = memory_query.group_by(MemoryModel.category).all()
        
        # Conversation trends by category
        conversation_query = db.query(
            ConversationModel.category,
            func.count(ConversationModel.id).label('count')
        ).filter(
            and_(
                ConversationModel.uid == uid,
                ConversationModel.discarded == False
            )
        )
        
        if start_date:
            conversation_query = conversation_query.filter(ConversationModel.created_at >= start_date)
        if end_date:
            conversation_query = conversation_query.filter(ConversationModel.created_at <= end_date)
            
        conversation_trends = conversation_query.group_by(ConversationModel.category).all()
        
        return {
            'memory_trends': [{'category': trend[0], 'count': trend[1]} for trend in memory_trends],
            'conversation_trends': [{'category': trend[0], 'count': trend[1]} for trend in conversation_trends]
        }
    finally:
        db.close()


def get_daily_activity(uid: str, days: int = 30):
    """Get daily activity for the last N days"""
    db = get_db_session()
    try:
        # Get daily memory count
        memory_query = db.query(
            func.date(MemoryModel.created_at).label('date'),
            func.count(MemoryModel.id).label('memories')
        ).filter(
            and_(
                MemoryModel.uid == uid,
                MemoryModel.discarded == False,
                MemoryModel.deleted == False,
                MemoryModel.created_at >= func.now() - func.interval(f'{days} days')
            )
        ).group_by(func.date(MemoryModel.created_at)).all()
        
        # Get daily conversation count
        conversation_query = db.query(
            func.date(ConversationModel.created_at).label('date'),
            func.count(ConversationModel.id).label('conversations')
        ).filter(
            and_(
                ConversationModel.uid == uid,
                ConversationModel.discarded == False,
                ConversationModel.created_at >= func.now() - func.interval(f'{days} days')
            )
        ).group_by(func.date(ConversationModel.created_at)).all()
        
        # Combine the data
        activity_dict = {}
        
        for date, count in memory_query:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in activity_dict:
                activity_dict[date_str] = {'memories': 0, 'conversations': 0}
            activity_dict[date_str]['memories'] = count
            
        for date, count in conversation_query:
            date_str = date.strftime('%Y-%m-%d')
            if date_str not in activity_dict:
                activity_dict[date_str] = {'memories': 0, 'conversations': 0}
            activity_dict[date_str]['conversations'] = count
        
        return [
            {'date': date, **data} 
            for date, data in sorted(activity_dict.items())
        ]
    finally:
        db.close()


def get_top_categories(uid: str, limit: int = 10):
    """Get top categories by frequency"""
    db = get_db_session()
    try:
        # Get top memory categories
        memory_categories = db.query(
            MemoryModel.category,
            func.count(MemoryModel.id).label('count')
        ).filter(
            and_(
                MemoryModel.uid == uid,
                MemoryModel.discarded == False,
                MemoryModel.deleted == False,
                MemoryModel.category.isnot(None)
            )
        ).group_by(MemoryModel.category).order_by(desc('count')).limit(limit).all()
        
        return [{'category': cat[0], 'count': cat[1]} for cat in memory_categories]
    finally:
        db.close()


def document_id_from_seed(seed: str) -> str:
    """Generate a document ID from a seed (placeholder implementation)"""
    import hashlib
    import uuid
    seed_hash = hashlib.sha256(seed.encode('utf-8')).digest()
    generated_uuid = uuid.UUID(bytes=seed_hash[:16], version=4)
    return str(generated_uuid)
