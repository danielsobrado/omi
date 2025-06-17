# backend/database/postgres/users.py
from datetime import datetime, timezone
from .client import get_db_session
from .models import User as UserModel


def is_exists_user(uid: str):
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        return user is not None
    finally:
        db.close()


def get_user_store_recording_permission(uid: str):
    # This would require adding a store_recording_permission field to the User model
    # For now, return default False
    return False


def set_user_store_recording_permission(uid: str, value: bool):
    # This would require adding a store_recording_permission field to the User model
    # For now, this is a no-op
    pass


def create_person(uid: str, data: dict):
    # This would require a separate people table
    # For now, return the data as-is
    return data


def get_person(uid: str, person_id: str):
    # This would require a separate people table
    # For now, return None
    return None


def get_people(uid: str):
    # This would require a separate people table
    # For now, return empty list
    return []


def update_person(uid: str, person_id: str, name: str):
    # This would require a separate people table
    # For now, this is a no-op
    pass


def create_user_if_not_exists(uid: str, email: str = None, display_name: str = None):
    """Create a user if they don't exist"""
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if not user:
            user = UserModel(
                uid=uid,
                email=email,
                display_name=display_name
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()


def get_user(uid: str):
    """Get user by uid"""
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if user:
            return {c.name: getattr(user, c.name) for c in user.__table__.columns}
        return None
    finally:
        db.close()


def update_user_data(uid: str, **kwargs):
    """Update user data"""
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()


def delete_user(uid: str):
    """Delete a user"""
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if user:
            db.delete(user)
            db.commit()
            return True
        return False
    finally:
        db.close()


# ************** Payments **************
# **************************************

def get_stripe_connect_account_id(uid: str):
    """Get the Stripe Connect account ID for a user"""
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if user:
            # Assuming there's a stripe_account_id field in the User model
            # If not present, this would return None
            return getattr(user, 'stripe_account_id', None)
        return None
    finally:
        db.close()


def set_stripe_connect_account_id(uid: str, account_id: str):
    """Set the Stripe Connect account ID for a user"""
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if user:
            # This would require adding stripe_account_id field to User model
            if hasattr(user, 'stripe_account_id'):
                user.stripe_account_id = account_id
                db.commit()
    finally:
        db.close()
