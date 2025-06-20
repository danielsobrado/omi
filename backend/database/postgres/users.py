# backend/database/postgres/users.py
import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Dict, Any, List, Optional

from sqlalchemy.exc import SQLAlchemyError

from .client import get_db_session
from .models import User as UserModel, Person as PersonModel, Rating as RatingModel
from database.utils import document_id_from_seed

# In a real app, this would be configured globally from a config file.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def db_session_manager(func):
    """
    A decorator to manage database sessions. It handles commits, rollbacks,
    and closing the session. It re-raises database errors to be handled by the caller.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        session = get_db_session()
        try:
            result = func(session, *args, **kwargs)
            session.commit()
            return result
        except SQLAlchemyError as e:
            logging.error(f"Database error in {func.__name__}: {e}", exc_info=True)
            session.rollback()
            # Re-raise the exception to be handled by a higher-level error handler
            raise
        finally:
            session.close()
    return wrapper


@db_session_manager
def is_exists_user(db, uid: str) -> bool:
    return db.query(UserModel).filter(UserModel.uid == uid).first() is not None


@db_session_manager
def get_user_store_recording_permission(db, uid: str) -> bool:
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    return user.store_recording_permission if user else False


@db_session_manager
def set_user_store_recording_permission(db, uid: str, value: bool) -> bool:
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        user.store_recording_permission = value
        logging.info(f"Set store_recording_permission to {value} for user {uid}")
        return True
    logging.warning(f"User {uid} not found when trying to set recording permission.")
    return False


@db_session_manager
def create_person(db, uid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    person = PersonModel(uid=uid, **data)
    db.add(person)
    db.flush()
    person_dict = {c.name: getattr(person, c.name) for c in person.__table__.columns}
    logging.info(f"Created person {data.get('id')} for user {uid}")
    return person_dict


@db_session_manager
def get_person(db, uid: str, person_id: str) -> Optional[Dict[str, Any]]:
    person = db.query(PersonModel).filter(PersonModel.uid == uid, PersonModel.id == person_id).first()
    return {c.name: getattr(person, c.name) for c in person.__table__.columns} if person else None


@db_session_manager
def get_people(db, uid: str) -> List[Dict[str, Any]]:
    people = db.query(PersonModel).filter(PersonModel.uid == uid).all()
    return [{c.name: getattr(p, c.name) for c in p.__table__.columns} for p in people]


@db_session_manager
def update_person(db, uid: str, person_id: str, name: str) -> bool:
    person = db.query(PersonModel).filter(PersonModel.uid == uid, PersonModel.id == person_id).first()
    if person:
        person.name = name
        return True
    return False


@db_session_manager
def delete_person(db, uid: str, person_id: str) -> bool:
    person = db.query(PersonModel).filter(PersonModel.uid == uid, PersonModel.id == person_id).first()
    if person:
        db.delete(person)
        return True
    return False


@db_session_manager
def delete_user_data(db, uid: str) -> Dict[str, str]:
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        db.delete(user)
        logging.info(f"Successfully deleted user {uid} and all associated data.")
        return {'status': 'ok', 'message': 'Account deleted successfully'}
    logging.warning(f"Attempted to delete non-existent user {uid}.")
    return {'status': 'error', 'message': 'User not found'}


@db_session_manager
def create_user_if_not_exists(db, uid: str, email: str = None, display_name: str = None) -> UserModel:
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if not user:
        user = UserModel(uid=uid, email=email, display_name=display_name)
        db.add(user)
        logging.info(f"Created new user: {uid} with email: {email}")
    return user


@db_session_manager
def get_user(db, uid: str) -> Optional[Dict[str, Any]]:
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    return {c.name: getattr(user, c.name) for c in user.__table__.columns} if user else None


@db_session_manager
def update_user_data(db, uid: str, **kwargs) -> bool:
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)
        logging.info(f"Updated user data for {uid} with keys: {list(kwargs.keys())}")
        return True
    logging.warning(f"User {uid} not found for update.")
    return False


def delete_user(uid: str) -> Dict[str, str]:
    return delete_user_data(uid)


# **************************************
# ************* Analytics **************
# **************************************

@db_session_manager
def set_conversation_summary_rating_score(db, uid: str, conversation_id: str, value: int):
    doc_id = document_id_from_seed('memory_summary' + conversation_id)
    rating = RatingModel(
        id=doc_id, uid=uid, entity_id=conversation_id,
        value=value, created_at=datetime.now(timezone.utc), type='memory_summary',
    )
    db.merge(rating) # Upsert
    return True


@db_session_manager
def set_chat_message_rating_score(db, uid: str, message_id: str, value: int):
    doc_id = document_id_from_seed('chat_message' + message_id)
    rating = RatingModel(
        id=doc_id, uid=uid, entity_id=message_id,
        value=value, created_at=datetime.now(timezone.utc), type='chat_message',
    )
    db.merge(rating) # Upsert
    return True

# ************** Payments **************
# **************************************

def get_stripe_connect_account_id(uid: str):
    user = get_user(uid)
    return user.get('stripe_account_id') if user else None


def set_stripe_connect_account_id(uid: str, account_id: str):
    return update_user_data(uid, stripe_account_id=account_id)


def set_paypal_payment_details(uid: str, data: dict):
    return update_user_data(uid, paypal_details=data)


def get_paypal_payment_details(uid: str):
    user = get_user(uid)
    return user.get('paypal_details') if user else None


def set_default_payment_method(uid: str, payment_method_id: str):
    return update_user_data(uid, default_payment_method=payment_method_id)


def get_default_payment_method(uid: str):
    user = get_user(uid)
    return user.get('default_payment_method') if user else None

# **************************************
# ************* Language ***************
# **************************************

def get_user_language_preference(uid: str) -> str:
    user = get_user(uid)
    return user.get('language', '') if user else ''


def set_user_language_preference(uid: str, language: str):
    return update_user_data(uid, language=language)