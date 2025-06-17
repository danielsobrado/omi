# backend/database/postgres/auth.py
from .client import get_db_session
from .models import User as UserModel
from database.redis_db import cache_user_name, get_cached_user_name


def get_user_from_uid(uid: str):
    if not uid:
        return None
        
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if user:
            return {
                'uid': user.uid,
                'email': user.email,
                'email_verified': True,  # Default for postgres users
                'phone_number': None,    # Not stored in our simple model
                'display_name': user.display_name,
                'photo_url': None,       # Not stored in our simple model
                'disabled': False,       # Default for postgres users
            }
        return None
    finally:
        db.close()


def get_user_name(uid: str, use_default: bool = True):
    # if cached_name := get_cached_user_name(uid):
    #     return cached_name
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


def create_user(uid: str, email: str, display_name: str = None):
    """Create a new user in the PostgreSQL database"""
    db = get_db_session()
    try:
        # Check if user already exists
        existing_user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if existing_user:
            return existing_user
            
        new_user = UserModel(
            uid=uid,
            email=email,
            display_name=display_name
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    finally:
        db.close()


def update_user(uid: str, **kwargs):
    """Update user information"""
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            db.commit()
            return user
        return None
    finally:
        db.close()
