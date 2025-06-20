# backend/database/postgres/notifications.py
import asyncio
import logging
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy import desc, and_
from sqlalchemy.orm import Session

from .client import db_session_manager, get_db_session
from .models import Notification as NotificationModel, User

@db_session_manager
def create_notification(db: Session, uid: str, notification_data: dict) -> Dict[str, Any]:
    notification = NotificationModel(uid=uid, **notification_data)
    db.add(notification)
    db.flush()
    return {c.name: getattr(notification, c.name) for c in notification.__table__.columns}

@db_session_manager
def get_notifications(db: Session, uid: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    notifications = (
        db.query(NotificationModel)
        .filter(NotificationModel.uid == uid)
        .order_by(desc(NotificationModel.created_at))
        .limit(limit).offset(offset).all()
    )
    return [{c.name: getattr(notif, c.name) for c in notif.__table__.columns} for notif in notifications]

@db_session_manager
def mark_notification_read(db: Session, notification_id: str) -> bool:
    notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()
    if notification:
        notification.is_read = True
        return True
    return False

@db_session_manager
def mark_all_notifications_read(db: Session, uid: str) -> int:
    updated_count = db.query(NotificationModel).filter(
        and_(NotificationModel.uid == uid, NotificationModel.is_read == False)
    ).update({'is_read': True}, synchronize_session=False)
    return updated_count

@db_session_manager
def get_unread_notifications_count(db: Session, uid: str) -> int:
    return db.query(NotificationModel).filter(
        and_(NotificationModel.uid == uid, NotificationModel.is_read == False)
    ).count()

@db_session_manager
def save_token(db: Session, uid: str, data: dict) -> None:
    user = db.query(User).filter(User.uid == uid).first()
    if user:
        for key, value in data.items():
            if hasattr(user, key):
                setattr(user, key, value)
    else:
        user_data = {'uid': uid, **data}
        db.add(User(**user_data))

@db_session_manager
def remove_token(db: Session, token: str) -> int:
    updated_count = db.query(User).filter(User.fcm_token == token).update(
        {'fcm_token': None, 'time_zone': None}, synchronize_session=False
    )
    return updated_count

async def get_users_in_timezones(timezones: List[str], filter_type: str) -> List:
    def sync_query():
        db = get_db_session()
        try:
            users_data = []
            query = db.query(User).filter(User.time_zone.in_(timezones), User.fcm_token.isnot(None))
            for user in query.all():
                if filter_type == 'fcm_token':
                    users_data.append(user.fcm_token)
                else:
                    users_data.append((user.uid, user.fcm_token))
            return users_data
        finally:
            db.close()
    return await asyncio.to_thread(sync_query)