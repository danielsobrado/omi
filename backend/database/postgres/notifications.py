# backend/database/postgres/notifications.py
from datetime import datetime
from typing import List
from sqlalchemy import desc, and_, text
from .client import get_db_session
from .models import Notification as NotificationModel, User


def create_notification(uid: str, notification_data: dict):
    """Create a new notification"""
    db = get_db_session()
    try:
        notification = NotificationModel(uid=uid, **notification_data)
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return {c.name: getattr(notification, c.name) for c in notification.__table__.columns}
    finally:
        db.close()


def get_notifications(uid: str, limit: int = 100, offset: int = 0):
    """Get notifications for a user"""
    db = get_db_session()
    try:
        notifications = (
            db.query(NotificationModel)
            .filter(NotificationModel.uid == uid)
            .order_by(desc(NotificationModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [{c.name: getattr(notif, c.name) for c in notif.__table__.columns} for notif in notifications]
    finally:
        db.close()


def get_notification(notification_id: str):
    """Get a specific notification"""
    db = get_db_session()
    try:
        notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()
        if notification:
            return {c.name: getattr(notification, c.name) for c in notification.__table__.columns}
        return None
    finally:
        db.close()


def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    db = get_db_session()
    try:
        notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()
        if notification:
            notification.is_read = True
            db.commit()
            return True
        return False
    finally:
        db.close()


def mark_all_notifications_read(uid: str):
    """Mark all notifications as read for a user"""
    db = get_db_session()
    try:
        notifications = db.query(NotificationModel).filter(
            and_(NotificationModel.uid == uid, NotificationModel.is_read == False)
        ).all()
        
        for notification in notifications:
            notification.is_read = True
        
        db.commit()
        return len(notifications)
    finally:
        db.close()


def delete_notification(notification_id: str):
    """Delete a notification"""
    db = get_db_session()
    try:
        notification = db.query(NotificationModel).filter(NotificationModel.id == notification_id).first()
        if notification:
            db.delete(notification)
            db.commit()
            return True
        return False
    finally:
        db.close()


def get_unread_notifications_count(uid: str):
    """Get count of unread notifications for a user"""
    db = get_db_session()
    try:
        count = db.query(NotificationModel).filter(
            and_(NotificationModel.uid == uid, NotificationModel.is_read == False)
        ).count()
        return count
    finally:
        db.close()


def save_token(uid: str, data: dict):
    """Save FCM token and user data"""
    db = get_db_session()
    try:
        user = db.query(User).filter(User.uid == uid).first()
        if user:
            # Update existing user
            for key, value in data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
        else:
            # Create new user with basic info
            user_data = {'uid': uid}
            user_data.update(data)
            user = User(**user_data)
            db.add(user)
        db.commit()
    finally:
        db.close()


def get_user_time_zone(uid: str):
    """Get user's timezone"""
    db = get_db_session()
    try:
        user = db.query(User).filter(User.uid == uid).first()
        return user.time_zone if user else None
    finally:
        db.close()


def get_token_only(uid: str):
    """Get only the FCM token for a user"""
    db = get_db_session()
    try:
        user = db.query(User).filter(User.uid == uid).first()
        return user.fcm_token if user else None
    finally:
        db.close()


def remove_token(token: str):
    """Remove FCM token from users"""
    db = get_db_session()
    try:
        users = db.query(User).filter(User.fcm_token == token).all()
        for user in users:
            user.fcm_token = None
            user.time_zone = None
        db.commit()
    finally:
        db.close()


def get_token(uid: str):
    """Get FCM token and timezone for a user"""
    db = get_db_session()
    try:
        user = db.query(User).filter(User.uid == uid).first()
        if user:
            return user.fcm_token, user.time_zone
        return None, None
    finally:
        db.close()


def store_pending_notification(notification_data: dict):
    """Store a pending notification for later delivery"""
    db = get_db_session()
    try:
        # Extract uid from token or notification data
        uid = notification_data.get('uid', 'system')
        
        # Create notification record matching the NotificationModel schema
        notification = NotificationModel(
            uid=uid,
            title=notification_data.get('title', ''),
            description=notification_data.get('body', notification_data.get('description', '')),
            token=notification_data.get('token'),
            type=notification_data.get('type', 'text'),
            app_id=notification_data.get('app_id'),
            scopes=notification_data.get('scopes', []),
            created_at=datetime.utcnow()
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return {c.name: getattr(notification, c.name) for c in notification.__table__.columns}
    finally:
        db.close()


async def get_users_token_in_timezones(timezones: List[str]):
    """Get FCM tokens for users in specific timezones"""
    return await get_users_in_timezones(timezones, 'fcm_token')


async def get_users_id_in_timezones(timezones: List[str]):
    """Get user IDs for users in specific timezones"""
    return await get_users_in_timezones(timezones, 'id')


async def get_users_in_timezones(timezones: List[str], filter_type: str):
    """Get users in specific timezones"""
    import asyncio
    
    def sync_query():
        db = get_db_session()
        try:
            users = []
            # PostgreSQL supports IN queries without the 30-item limit
            query = db.query(User).filter(User.time_zone.in_(timezones))
            
            for user in query.all():
                if not user.fcm_token:
                    continue
                    
                if filter_type == 'fcm_token':
                    token = user.fcm_token
                else:
                    token = (user.uid, user.fcm_token)
                
                if token:
                    users.append(token)
            
            return users
        finally:
            db.close()
    
    return await asyncio.to_thread(sync_query)
