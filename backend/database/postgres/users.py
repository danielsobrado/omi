# backend/database/postgres/users.py
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy import desc, and_, or_
from sqlalchemy.orm import Session

from database.helpers import prepare_for_write, prepare_for_read
from .client import db_session_manager
from .models import (
    User as UserModel, 
    Person as PersonModel, 
    Rating as RatingModel,
    Conversation as ConversationModel,
    Message as MessageModel,
    Memory as MemoryModel,
    ChatSession as ChatSessionModel,
    File as FileModel
)
from .client import document_id_from_seed

# *****************************
# ********** USER CRUD ********
# *****************************

@db_session_manager
def is_exists_user(db: Session, uid: str) -> bool:
    return db.query(UserModel).filter(UserModel.uid == uid).first() is not None

@db_session_manager
def get_user_profile(db: Session, uid: str) -> dict:
    """Gets the full user profile document."""
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        return {c.name: getattr(user, c.name) for c in user.__table__.columns}
    return {}

@db_session_manager
def get_user_store_recording_permission(db: Session, uid: str) -> bool:
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    return getattr(user, 'store_recording_permission', False) if user else False

@db_session_manager
def set_user_store_recording_permission(db: Session, uid: str, value: bool):
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        user.store_recording_permission = value
        db.flush()
    else:
        # Create user if doesn't exist
        user = UserModel(uid=uid, store_recording_permission=value)
        db.add(user)
        db.flush()

# *****************************
# ********* PEOPLE ************
# *****************************

@db_session_manager
def create_person(db: Session, uid: str, data: dict):
    model_columns = {c.name for c in PersonModel.__table__.columns}
    filtered_data = {k: v for k, v in data.items() if k in model_columns}
    
    person = PersonModel(uid=uid, **filtered_data)
    db.add(person)
    db.flush()
    return {c.name: getattr(person, c.name) for c in person.__table__.columns}

@db_session_manager
def get_person(db: Session, uid: str, person_id: str):
    person = db.query(PersonModel).filter(
        and_(PersonModel.uid == uid, PersonModel.id == person_id)
    ).first()
    
    if person:
        return {c.name: getattr(person, c.name) for c in person.__table__.columns}
    return None

@db_session_manager
def get_people(db: Session, uid: str):
    people = db.query(PersonModel).filter(PersonModel.uid == uid).all()
    return [{c.name: getattr(p, c.name) for c in p.__table__.columns} for p in people]

@db_session_manager
def update_person(db: Session, uid: str, person_id: str, name: str):
    person = db.query(PersonModel).filter(
        and_(PersonModel.uid == uid, PersonModel.id == person_id)
    ).first()
    
    if person:
        person.name = name
        db.flush()

@db_session_manager
def delete_person(db: Session, uid: str, person_id: str):
    person = db.query(PersonModel).filter(
        and_(PersonModel.uid == uid, PersonModel.id == person_id)
    ).first()
    
    if person:
        db.delete(person)
        db.flush()

@db_session_manager
def delete_user_data(db: Session, uid: str):
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if not user:
        return {'status': 'error', 'message': 'User not found'}

    # Delete all related data in batches
    subcollections = [
        (ConversationModel, 'conversations'),
        (MessageModel, 'messages'), 
        (ChatSessionModel, 'chat_sessions'),
        (PersonModel, 'people'),
        (MemoryModel, 'memories'),
        (FileModel, 'files'),
        (RatingModel, 'ratings')
    ]
    
    batch_size = 450
    
    for model_class, collection_name in subcollections:
        logging.info(f"Deleting {collection_name} for user {uid}")
        
        while True:
            items = db.query(model_class).filter(model_class.uid == uid).limit(batch_size).all()
            
            if not items:
                logging.info(f"No more {collection_name} to delete")
                break
                
            for item in items:
                logging.info(f"Deleting {collection_name} item: {item.id}")
                db.delete(item)
            
            db.commit()  # Commit batch
            
            if len(items) < batch_size:
                logging.info(f"Processed all {collection_name}")
                break

    # Delete the user document itself
    logging.info(f"Deleting user document: {uid}")
    db.delete(user)
    db.flush()
    
    return {'status': 'ok', 'message': 'Account deleted successfully'}

# **************************************
# ************* Analytics **************
# **************************************

@db_session_manager
def set_conversation_summary_rating_score(db: Session, uid: str, conversation_id: str, value: int):
    doc_id = document_id_from_seed('memory_summary' + conversation_id)
    
    # Check if rating exists
    existing = db.query(RatingModel).filter(RatingModel.id == doc_id).first()
    
    if existing:
        existing.value = value
        existing.updated_at = datetime.now(timezone.utc)
    else:
        rating = RatingModel(
            id=doc_id,
            uid=uid,
            entity_id=conversation_id,
            value=value,
            created_at=datetime.now(timezone.utc),
            type='memory_summary'
        )
        db.add(rating)
    
    db.flush()

@db_session_manager
def get_conversation_summary_rating_score(db: Session, conversation_id: str):
    doc_id = document_id_from_seed('memory_summary' + conversation_id)
    rating = db.query(RatingModel).filter(RatingModel.id == doc_id).first()
    
    if rating:
        return {c.name: getattr(rating, c.name) for c in rating.__table__.columns}
    return None

@db_session_manager
def get_all_ratings(db: Session, rating_type: str = 'memory_summary'):
    ratings = db.query(RatingModel).filter(RatingModel.type == rating_type).all()
    return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in ratings]

@db_session_manager
def set_chat_message_rating_score(db: Session, uid: str, message_id: str, value: int):
    doc_id = document_id_from_seed('chat_message' + message_id)
    
    # Check if rating exists
    existing = db.query(RatingModel).filter(RatingModel.id == doc_id).first()
    
    if existing:
        existing.value = value
        existing.updated_at = datetime.now(timezone.utc)
    else:
        rating = RatingModel(
            id=doc_id,
            uid=uid,
            entity_id=message_id,
            value=value,
            created_at=datetime.now(timezone.utc),
            type='chat_message'
        )
        db.add(rating)
    
    db.flush()

# **************************************
# ************** Payments **************
# **************************************

@db_session_manager
def get_stripe_connect_account_id(db: Session, uid: str):
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    return getattr(user, 'stripe_account_id', None) if user else None

@db_session_manager
def set_stripe_connect_account_id(db: Session, uid: str, account_id: str):
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        user.stripe_account_id = account_id
        db.flush()
    else:
        # Create user if doesn't exist
        user = UserModel(uid=uid, stripe_account_id=account_id)
        db.add(user)
        db.flush()

@db_session_manager
def set_paypal_payment_details(db: Session, uid: str, data: dict):
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        user.paypal_details = data
        db.flush()
    else:
        # Create user if doesn't exist
        user = UserModel(uid=uid, paypal_details=data)
        db.add(user)
        db.flush()

@db_session_manager
def get_paypal_payment_details(db: Session, uid: str):
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    return getattr(user, 'paypal_details', None) if user else None

@db_session_manager
def set_default_payment_method(db: Session, uid: str, payment_method_id: str):
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        user.default_payment_method = payment_method_id
        db.flush()
    else:
        # Create user if doesn't exist
        user = UserModel(uid=uid, default_payment_method=payment_method_id)
        db.add(user)
        db.flush()

@db_session_manager
def get_default_payment_method(db: Session, uid: str):
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    return getattr(user, 'default_payment_method', None) if user else None

# **************************************
# ********* Data Protection ************
# **************************************

@db_session_manager
def get_data_protection_level(db: Session, uid: str) -> str:
    """
    Get the user's data protection level.

    Args:
        uid: User ID

    Returns:
        'enhanced' or 'e2ee'. Defaults to 'enhanced'.
    """
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    
    if user:
        return getattr(user, 'data_protection_level', 'enhanced')
    
    return 'enhanced'

@db_session_manager
def set_data_protection_level(db: Session, uid: str, level: str) -> None:
    """
    Set the user's data protection level.

    Args:
        uid: User ID
        level: 'enhanced', or 'e2ee'
    """
    if level not in ['enhanced', 'e2ee']:
        raise ValueError("Invalid data protection level. Only 'enhanced' or 'e2ee' are supported.")
    
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        user.data_protection_level = level
        db.flush()
    else:
        # Create user if doesn't exist
        user = UserModel(uid=uid, data_protection_level=level)
        db.add(user)
        db.flush()

@db_session_manager
def set_migration_status(db: Session, uid: str, target_level: str):
    """Sets the migration status on the user's profile."""
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    
    migration_status = {
        'target_level': target_level,
        'status': 'in_progress',
        'started_at': datetime.now(timezone.utc).isoformat()
    }
    
    if user:
        user.migration_status = migration_status
        db.flush()
    else:
        # Create user if doesn't exist
        user = UserModel(uid=uid, migration_status=migration_status)
        db.add(user)
        db.flush()

@db_session_manager
def finalize_migration(db: Session, uid: str, target_level: str):
    """Atomically sets the new protection level and removes the migration status field."""
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    
    if user:
        user.data_protection_level = target_level
        user.migration_status = None  # Remove migration status
        db.flush()

# **************************************
# ************* Language ***************
# **************************************

@db_session_manager
def get_user_language_preference(db: Session, uid: str) -> str:
    """
    Get the user's preferred language.
    
    Args:
        uid: User ID
        
    Returns:
        Language code (e.g., 'en', 'vi') or empty string if not set
    """
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    
    if user:
        return getattr(user, 'language', '') or ''
    
    return ''  # Return empty string if not set

@db_session_manager
def set_user_language_preference(db: Session, uid: str, language: str) -> None:
    """
    Set the user's preferred language.
    
    Args:
        uid: User ID
        language: Language code (e.g., 'en', 'vi')
    """
    user = db.query(UserModel).filter(UserModel.uid == uid).first()
    if user:
        user.language = language
        db.flush()
    else:
        # Create user if doesn't exist
        user = UserModel(uid=uid, language=language)
        db.add(user)
        db.flush()