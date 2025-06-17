# backend/database/postgres/apps.py
import os
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, text
import json

from .client import get_db_session
from .models import App as AppModel, User as UserModel, Tester as TesterModel, AppUsageHistory as AppUsageHistoryModel
from database.redis_db import get_app_reviews
from models.app import UsageHistoryType

# *****************************
# ********** CRUD *************
# *****************************

def migrate_reviews_from_redis_to_firestore():
    # This function is Firestore-specific, keeping as placeholder
    pass


def get_app_by_id_db(app_id: str):
    db = get_db_session()
    try:
        app = db.query(AppModel).filter(AppModel.id == app_id).first()
        if app:
            # Convert SQLAlchemy model to dict to match Firestore's output
            app_dict = {c.name: getattr(app, c.name) for c in app.__table__.columns}
            return app_dict
        return None
    finally:
        db.close()


def get_audio_apps_count(app_ids: List[str]):
    if not app_ids or len(app_ids) == 0:
        return 0
    
    db = get_db_session()
    try:
        # Query for apps with audio_bytes trigger
        count = db.query(AppModel).filter(
            and_(
                AppModel.id.in_(app_ids),
                AppModel.external_integration['triggers_on'].astext == 'audio_bytes'
            )
        ).count()
        return count
    finally:
        db.close()


def get_private_apps_db(uid: str) -> List:
    db = get_db_session()
    try:
        apps = db.query(AppModel).filter(
            and_(AppModel.uid == uid, AppModel.private == True)
        ).all()
        return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]
    finally:
        db.close()


def get_unapproved_public_apps_db() -> List:
    db = get_db_session()
    try:
        apps = db.query(AppModel).filter(
            and_(AppModel.approved == False, AppModel.private == False)
        ).all()
        return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]
    finally:
        db.close()


def get_all_unapproved_apps_db() -> List:
    db = get_db_session()
    try:
        apps = db.query(AppModel).filter(AppModel.approved == False).all()
        return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]
    finally:
        db.close()


def get_public_apps_db(uid: str) -> List:
    db = get_db_session()
    try:
        # Get all apps that are either approved or belong to the user
        apps = db.query(AppModel).filter(
            or_(AppModel.approved == True, AppModel.uid == uid)
        ).all()
        return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]
    finally:
        db.close()


def get_public_approved_apps_db() -> List:
    db = get_db_session()
    try:
        apps = db.query(AppModel).filter(
            and_(AppModel.approved == True, AppModel.private == False)
        ).all()
        return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]
    finally:
        db.close()


def get_popular_apps_db() -> List:
    db = get_db_session()
    try:
        apps = db.query(AppModel).filter(
            and_(AppModel.approved == True, AppModel.is_popular == True)
        ).all()
        return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]
    finally:
        db.close()


def set_app_popular_db(app_id: str, popular: bool):
    db = get_db_session()
    try:
        app = db.query(AppModel).filter(AppModel.id == app_id).first()
        if app:
            app.is_popular = popular
            db.commit()
    finally:
        db.close()


def get_public_unapproved_apps_db(uid: str) -> List:
    db = get_db_session()
    try:
        apps = db.query(AppModel).filter(
            and_(
                AppModel.approved == False, 
                AppModel.uid == uid,
                AppModel.private == False
            )
        ).all()
        return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]
    finally:
        db.close()


def get_apps_for_tester_db(uid: str) -> List:
    # This function requires a testers table that we haven't implemented yet
    # For now, return empty list
    return []


def add_app_to_db(app_data: dict):
    db = get_db_session()
    try:
        new_app = AppModel(**app_data)
        db.add(new_app)
        db.commit()
    finally:
        db.close()


def upsert_app_to_db(app_data: dict):
    db = get_db_session()
    try:
        existing_app = db.query(AppModel).filter(AppModel.id == app_data['id']).first()
        if existing_app:
            # Update existing app
            for key, value in app_data.items():
                if hasattr(existing_app, key):
                    setattr(existing_app, key, value)
        else:
            # Create new app
            new_app = AppModel(**app_data)
            db.add(new_app)
        db.commit()
    finally:
        db.close()


def update_app_in_db(app_data: dict):
    db = get_db_session()
    try:
        app = db.query(AppModel).filter(AppModel.id == app_data['id']).first()
        if app:
            for key, value in app_data.items():
                if hasattr(app, key):
                    setattr(app, key, value)
            db.commit()
    finally:
        db.close()


def delete_app_from_db(app_id: str):
    db = get_db_session()
    try:
        app = db.query(AppModel).filter(AppModel.id == app_id).first()
        if app:
            db.delete(app)
            db.commit()
    finally:
        db.close()


def update_app_visibility_in_db(app_id: str, private: bool):
    db = get_db_session()
    try:
        app = db.query(AppModel).filter(AppModel.id == app_id).first()
        if app:
            app.private = private
            db.commit()
    finally:
        db.close()


def change_app_approval_status(app_id: str, approved: bool):
    db = get_db_session()
    try:
        app = db.query(AppModel).filter(AppModel.id == app_id).first()
        if app:
            app.approved = approved
            app.status = 'approved' if approved else 'rejected'
            db.commit()
    finally:
        db.close()


# Usage history functions - simplified for now
def get_app_usage_history_db(app_id: str):
    # This would require a separate usage_history table
    return []


def get_app_memory_created_integration_usage_count_db(app_id: str):
    # This would require a separate usage_history table
    return 0


def get_app_memory_prompt_usage_count_db(app_id: str):
    # This would require a separate usage_history table
    return 0


def get_app_chat_message_sent_usage_count_db(app_id: str):
    # This would require a separate usage_history table
    return 0


def get_app_usage_count_db(app_id: str):
    # This would require a separate usage_history table
    return 0


# ********************************
# *********** REVIEWS ************
# ********************************

def set_app_review_in_db(app_id: str, uid: str, review: dict):
    db = get_db_session()
    try:
        app = db.query(AppModel).filter(AppModel.id == app_id).first()
        if app:
            # For now, store reviews as JSON in the app model
            # In a more sophisticated setup, you'd have a separate reviews table
            if app.reviews is None:
                app.reviews = []
            
            # Remove existing review from this user if any
            app.reviews = [r for r in app.reviews if r.get('uid') != uid]
            # Add new review
            app.reviews.append(review)
            db.commit()
    finally:
        db.close()


# ********************************
# ************ TESTER ************
# ********************************

def get_apps_for_tester_db(uid: str) -> List:
    db = get_db_session()
    try:
        tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
        if not tester or not tester.apps:
            return []
        
        # Get all apps this tester has access to
        apps = db.query(AppModel).filter(AppModel.id.in_(tester.apps)).all()
        return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]
    finally:
        db.close()


def add_tester_db(data: dict):
    db = get_db_session()
    try:
        tester = TesterModel(
            uid=data['uid'],
            apps=data.get('apps', [])
        )
        db.add(tester)
        db.commit()
    finally:
        db.close()


def add_app_access_for_tester_db(app_id: str, uid: str):
    db = get_db_session()
    try:
        tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
        if tester:
            if tester.apps is None:
                tester.apps = []
            if app_id not in tester.apps:
                tester.apps.append(app_id)
                # SQLAlchemy needs to know the array changed
                tester.apps = list(tester.apps)
                db.commit()
        else:
            # Create new tester with this app
            new_tester = TesterModel(uid=uid, apps=[app_id])
            db.add(new_tester)
            db.commit()
    finally:
        db.close()


def remove_app_access_for_tester_db(app_id: str, uid: str):
    db = get_db_session()
    try:
        tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
        if tester and tester.apps and app_id in tester.apps:
            tester.apps.remove(app_id)
            # SQLAlchemy needs to know the array changed
            tester.apps = list(tester.apps)
            db.commit()
    finally:
        db.close()


def remove_tester_db(uid: str):
    db = get_db_session()
    try:
        tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
        if tester:
            db.delete(tester)
            db.commit()
    finally:
        db.close()


def can_tester_access_app_db(app_id: str, uid: str) -> bool:
    db = get_db_session()
    try:
        tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
        if tester and tester.apps:
            return app_id in tester.apps
        return False
    finally:
        db.close()


def is_tester_db(uid: str) -> bool:
    db = get_db_session()
    try:
        tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
        return tester is not None
    finally:
        db.close()


# ********************************
# *********** APPS USAGE *********
# ********************************

def record_app_usage(
        uid: str, app_id: str, usage_type: UsageHistoryType, conversation_id: str = None, message_id: str = None,
        timestamp: datetime = None
):
    if not conversation_id and not message_id:
        raise ValueError('conversation_id or message_id must be provided')

    db = get_db_session()
    try:
        usage_data = {
            'uid': uid,
            'app_id': app_id,
            'usage_type': usage_type.value,
            'conversation_id': conversation_id,
            'message_id': message_id,
            'timestamp': datetime.now(timezone.utc) if timestamp is None else timestamp,
        }
        new_usage = AppUsageHistoryModel(**usage_data)
        db.add(new_usage)
        db.commit()
        db.refresh(new_usage)
        # return as dict to match firestore's output
        return {c.name: getattr(new_usage, c.name) for c in new_usage.__table__.columns}
    finally:
        db.close()

# Additional functions that may be needed but not in the original file
def get_all_apps_db() -> List:
    db = get_db_session()
    try:
        apps = db.query(AppModel).all()
        return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]
    finally:
        db.close()


def get_apps_by_user_db(uid: str) -> List:
    db = get_db_session()
    try:
        apps = db.query(AppModel).filter(AppModel.uid == uid).all()
        return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]
    finally:
        db.close()


def get_persona_by_uid_db(uid: str):
    """Get a persona app by user ID"""
    with Session() as session:
        result = session.execute(
            text("""
                SELECT * FROM plugins_data 
                WHERE uid = :uid 
                AND capabilities @> '["persona"]'::jsonb
                LIMIT 1
            """),
            {"uid": uid}
        )
        row = result.fetchone()
        if row:
            # Convert row to dict
            return dict(row._mapping)
        return None


def get_omi_personas_by_uid_db(uid: str):
    """Get OMI personas by user ID"""
    with Session() as session:
        result = session.execute(
            text("""
                SELECT * FROM plugins_data 
                WHERE uid = :uid 
                AND capabilities @> '["persona"]'::jsonb
                AND connected_accounts @> '["omi"]'::jsonb
            """),
            {"uid": uid}
        )
        return [dict(row._mapping) for row in result.fetchall()]


def update_persona_in_db(persona_data: dict):
    """Update a persona in the database"""
    if 'id' not in persona_data:
        raise ValueError("Persona data must include 'id' field")
    
    persona_id = persona_data.pop('id')
    
    with Session() as session:
        # Convert dict to SET clauses for update
        set_clauses = []
        params = {"id": persona_id}
        
        for key, value in persona_data.items():
            if isinstance(value, (dict, list)):
                set_clauses.append(f"{key} = :{key}::jsonb")
                params[key] = json.dumps(value)
            else:
                set_clauses.append(f"{key} = :{key}")
                params[key] = value
        
        if set_clauses:
            query = f"""
                UPDATE plugins_data 
                SET {', '.join(set_clauses)}
                WHERE id = :id
            """
            session.execute(text(query), params)
            session.commit()


def get_api_key_by_hash_db(app_id: str, hashed_key: str):
    """Get an API key by its hash value"""
    # Note: This function requires a separate api_keys table or structure
    # For now, implementing as a placeholder that returns None
    # This would need to be properly implemented based on the actual API key storage structure
    return None


def get_popular_apps_db() -> List:
    """Get popular approved apps"""
    with Session() as session:
        result = session.execute(
            text("""
                SELECT * FROM plugins_data 
                WHERE approved = true 
                AND is_popular = true
            """)
        )
        return [dict(row._mapping) for row in result.fetchall()]


def get_persona_by_id_db(persona_id: str):
    """Get a persona by ID"""
    db = get_db_session()
    try:
        app = db.query(AppModel).filter(AppModel.id == persona_id).first()
        if app:
            return {c.name: getattr(app, c.name) for c in app.__table__.columns}
        return None
    finally:
        db.close()


def get_persona_by_username_twitter_handle_db(username: str, handle: str):
    """Get a persona by username and Twitter handle"""
    db = get_db_session()
    try:
        app = db.query(AppModel).filter(
            and_(
                AppModel.username == username,
                AppModel.category == 'personality-emulation',
                AppModel.twitter['username'].astext == handle
            )
        ).first()
        if app:
            app_dict = {c.name: getattr(app, c.name) for c in app.__table__.columns}
            return {'id': app.id, **app_dict}
        return None
    finally:
        db.close()