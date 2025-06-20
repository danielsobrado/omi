# backend/database/postgres/auth.py
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from .client import db_session_manager
from .models import User as UserModel
from database.redis_db import cache_user_name

@db_session_manager
def get_user_from_uid(db: Session, uid: str) -> Optional[Dict[str, Any]]:
    if not uid:
        return None
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        return {
            'uid': user.uid, 'email': user.email, 'email_verified': True,
            'phone_number': None, 'display_name': user.display_name,
            'photo_url': None, 'disabled': False,
        }
    return None

def get_user_name(uid: str, use_default: bool = True) -> str:
    default_name = 'The User' if use_default else None
    user = get_user_from_uid(uid)
    if not user:
        return default_name
    display_name = user.get('display_name')
    if not display_name:
        return default_name
    display_name = display_name.split(' ')[0]
    if display_name == 'AnonymousUser':
        display_name = default_name
    cache_user_name(uid, display_name, ttl=60 * 60)
    return display_name

@db_session_manager
def create_user(db: Session, uid: str, email: str, display_name: str = None) -> UserModel:
    existing_user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if existing_user:
        return existing_user
    new_user = UserModel(uid=uid, email=email, display_name=display_name)
    db.add(new_user)
    db.flush()
    return new_user

@db_session_manager
def update_user(db: Session, uid: str, **kwargs) -> Optional[UserModel]:
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        db.flush()
        return user
    return None