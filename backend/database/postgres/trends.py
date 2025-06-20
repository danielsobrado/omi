# backend/database/postgres/trends.py
from datetime import datetime
from typing import List, Dict
from sqlalchemy import func, desc, and_
from sqlalchemy.orm import Session

from .client import db_session_manager
from .models import Memory as MemoryModel, Conversation as ConversationModel
from database.utils import document_id_from_seed

@db_session_manager
def get_trends_data(db: Session, uid: str, start_date: datetime = None, end_date: datetime = None) -> Dict[str, List]:
    # Memory trends
    mem_query = db.query(MemoryModel.category, func.count(MemoryModel.id).label('count')).filter(
        and_(MemoryModel.uid == uid, MemoryModel.discarded == False, MemoryModel.deleted == False)
    )
    if start_date: mem_query = mem_query.filter(MemoryModel.created_at >= start_date)
    if end_date: mem_query = mem_query.filter(MemoryModel.created_at <= end_date)
    memory_trends = mem_query.group_by(MemoryModel.category).all()

    # Conversation trends
    conv_query = db.query(ConversationModel.category, func.count(ConversationModel.id).label('count')).filter(
        and_(ConversationModel.uid == uid, ConversationModel.discarded == False)
    )
    if start_date: conv_query = conv_query.filter(ConversationModel.created_at >= start_date)
    if end_date: conv_query = conv_query.filter(ConversationModel.created_at <= end_date)
    conversation_trends = conv_query.group_by(ConversationModel.category).all()

    return {
        'memory_trends': [{'category': trend[0], 'count': trend[1]} for trend in memory_trends],
        'conversation_trends': [{'category': trend[0], 'count': trend[1]} for trend in conversation_trends]
    }

@db_session_manager
def get_daily_activity(db: Session, uid: str, days: int = 30) -> List[Dict[str, Any]]:
    activity_dict = {}
    
    # Memory activity
    mem_activity = db.query(
        func.date(MemoryModel.created_at).label('date'),
        func.count(MemoryModel.id).label('memories')
    ).filter(
        and_(
            MemoryModel.uid == uid, MemoryModel.discarded == False, MemoryModel.deleted == False,
            MemoryModel.created_at >= func.now() - func.interval(f'{days} days')
        )
    ).group_by(func.date(MemoryModel.created_at)).all()

    for date, count in mem_activity:
        date_str = date.strftime('%Y-%m-%d')
        activity_dict.setdefault(date_str, {'memories': 0, 'conversations': 0})['memories'] = count

    # Conversation activity
    conv_activity = db.query(
        func.date(ConversationModel.created_at).label('date'),
        func.count(ConversationModel.id).label('conversations')
    ).filter(
        and_(
            ConversationModel.uid == uid, ConversationModel.discarded == False,
            ConversationModel.created_at >= func.now() - func.interval(f'{days} days')
        )
    ).group_by(func.date(ConversationModel.created_at)).all()

    for date, count in conv_activity:
        date_str = date.strftime('%Y-%m-%d')
        activity_dict.setdefault(date_str, {'memories': 0, 'conversations': 0})['conversations'] = count
    
    return [{'date': date, **data} for date, data in sorted(activity_dict.items())]

@db_session_manager
def get_top_categories(db: Session, uid: str, limit: int = 10) -> List[Dict[str, Any]]:
    memory_categories = db.query(
        MemoryModel.category, func.count(MemoryModel.id).label('count')
    ).filter(
        and_(
            MemoryModel.uid == uid, MemoryModel.discarded == False, MemoryModel.deleted == False,
            MemoryModel.category.isnot(None)
        )
    ).group_by(MemoryModel.category).order_by(desc('count')).limit(limit).all()
    
    return [{'category': cat[0], 'count': cat[1]} for cat in memory_categories]