# backend/database/postgres/users.py
from datetime import datetime, timezone
from .client import get_db_session
from .models import User as UserModel, Person as PersonModel, Rating as RatingModel
from database.utils import document_id_from_seed


def is_exists_user(uid: str):
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        return user is not None
    finally:
        db.close()


def get_user_store_recording_permission(uid: str):
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        return user.store_recording_permission if user else False
    finally:
        db.close()


def set_user_store_recording_permission(uid: str, value: bool):
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if user:
            user.store_recording_permission = value
            db.commit()
    finally:
        db.close()


def create_person(uid: str, data: dict):
    db = get_db_session()
    try:
        person = PersonModel(uid=uid, **data)
        db.add(person)
        db.commit()
        db.refresh(person)
        return {c.name: getattr(person, c.name) for c in person.__table__.columns}
    finally:
        db.close()


def get_person(uid: str, person_id: str):
    db = get_db_session()
    try:
        person = db.query(PersonModel).filter(PersonModel.uid == uid, PersonModel.id == person_id).first()
        if person:
            return {c.name: getattr(person, c.name) for c in person.__table__.columns}
        return None
    finally:
        db.close()


def get_people(uid: str):
    db = get_db_session()
    try:
        people = db.query(PersonModel).filter(PersonModel.uid == uid).all()
        return [{c.name: getattr(p, c.name) for c in p.__table__.columns} for p in people]
    finally:
        db.close()


def update_person(uid: str, person_id: str, name: str):
    db = get_db_session()
    try:
        person = db.query(PersonModel).filter(PersonModel.uid == uid, PersonModel.id == person_id).first()
        if person:
            person.name = name
            db.commit()
    finally:
        db.close()


def delete_person(uid: str, person_id: str):
    db = get_db_session()
    try:
        person = db.query(PersonModel).filter(PersonModel.uid == uid, PersonModel.id == person_id).first()
        if person:
            db.delete(person)
            db.commit()
    finally:
        db.close()


def delete_user_data(uid: str):
    """Deletes a user and all their associated data using cascading deletes."""
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if user:
            db.delete(user)
            db.commit()
            return {'status': 'ok', 'message': 'Account deleted successfully'}
        return {'status': 'error', 'message': 'User not found'}
    finally:
        db.close()


def create_user_if_not_exists(uid: str, email: str = None, display_name: str = None):
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if not user:
            user = UserModel(uid=uid, email=email, display_name=display_name)
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    finally:
        db.close()


def get_user(uid: str):
    db = get_db_session()
    try:
        user = db.query(UserModel).filter(UserModel.uid == uid).first()
        if user:
            return {c.name: getattr(user, c.name) for c in user.__table__.columns}
        return None
    finally:
        db.close()


def update_user_data(uid: str, **kwargs):
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
    return delete_user_data(uid)


# **************************************
# ************* Analytics **************
# **************************************

def set_conversation_summary_rating_score(uid: str, conversation_id: str, value: int):
    doc_id = document_id_from_seed('memory_summary' + conversation_id)
    db = get_db_session()
    try:
        rating = RatingModel(
            id=doc_id,
            uid=uid,
            entity_id=conversation_id,
            value=value,
            created_at=datetime.now(timezone.utc),
            type='memory_summary',
        )
        db.merge(rating) # Upsert
        db.commit()
    finally:
        db.close()


def set_chat_message_rating_score(uid: str, message_id: str, value: int):
    doc_id = document_id_from_seed('chat_message' + message_id)
    db = get_db_session()
    try:
        rating = RatingModel(
            id=doc_id,
            uid=uid,
            entity_id=message_id,
            value=value,
            created_at=datetime.now(timezone.utc),
            type='chat_message',
        )
        db.merge(rating) # Upsert
        db.commit()
    finally:
        db.close()

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