# backend/database/postgres/apps.py
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from .client import db_session_manager
from .models import App as AppModel, Tester as TesterModel, AppUsageHistory as AppUsageHistoryModel, ApiKey as ApiKeyModel
from models.app import UsageHistoryType

# *****************************
# ********** BASIC CRUD *******
# *****************************

@db_session_manager
def get_app_by_id_db(db: Session, app_id: str) -> Optional[Dict[str, Any]]:
    app = db.query(AppModel).filter(AppModel.id == app_id).first()
    if app:
        return {c.name: getattr(app, c.name) for c in app.__table__.columns}
    return None

@db_session_manager
def add_app_to_db(db: Session, app_data: dict):
    app = AppModel(**app_data)
    db.add(app)
    db.flush()
    logging.info(f"Added app with ID: {app_data.get('id')}")

@db_session_manager
def upsert_app_to_db(db: Session, app_data: Dict[str, Any]) -> None:
    db.merge(AppModel(**app_data))
    db.flush()
    logging.info(f"Upserted app with ID: {app_data.get('id')}")

@db_session_manager
def update_app_in_db(db: Session, app_data: Dict[str, Any]) -> bool:
    app = db.query(AppModel).filter(AppModel.id == app_data['id']).first()
    if app:
        for key, value in app_data.items():
            if hasattr(app, key):
                setattr(app, key, value)
        db.flush()
        logging.info(f"Updated app with ID: {app_data.get('id')}")
        return True
    return False

@db_session_manager
def delete_app_from_db(db: Session, app_id: str) -> bool:
    app = db.query(AppModel).filter(AppModel.id == app_id).first()
    if app:
        db.delete(app)
        db.flush()
        logging.info(f"Deleted app with ID: {app_id}")
        return True
    return False

# *****************************
# ******** APP QUERIES ********
# *****************************

@db_session_manager
def get_audio_apps_count(db: Session, app_ids: List[str]) -> int:
    if not app_ids:
        return 0
    count = db.query(AppModel).filter(
        and_(
            AppModel.id.in_(app_ids),
            AppModel.external_integration.op('->>')('triggers_on') == 'audio_bytes'
        )
    ).count()
    return count

@db_session_manager
def get_private_apps_db(db: Session, uid: str) -> List[Dict[str, Any]]:
    apps = db.query(AppModel).filter(and_(AppModel.uid == uid, AppModel.private == True)).all()
    return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]

@db_session_manager
def get_public_apps_db(db: Session, uid: str) -> List[Dict[str, Any]]:
    apps = db.query(AppModel).filter(or_(AppModel.approved == True, AppModel.uid == uid)).all()
    return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]

@db_session_manager
def get_public_approved_apps_db(db: Session) -> List[Dict[str, Any]]:
    apps = db.query(AppModel).filter(and_(AppModel.approved == True, AppModel.private == False)).all()
    return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]

@db_session_manager
def get_popular_apps_db(db: Session) -> List[Dict[str, Any]]:
    apps = db.query(AppModel).filter(and_(AppModel.approved == True, AppModel.is_popular == True)).all()
    return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]

@db_session_manager
def get_unapproved_public_apps_db(db: Session) -> List[Dict[str, Any]]:
    """Get public apps that are not yet approved (all users)."""
    apps = db.query(AppModel).filter(
        and_(AppModel.approved == False, AppModel.private == False)
    ).all()
    return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]

@db_session_manager
def get_all_unapproved_apps_db(db: Session) -> List[Dict[str, Any]]:
    """Get all unapproved apps including private ones."""
    apps = db.query(AppModel).filter(AppModel.approved == False).all()
    return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]

@db_session_manager
def get_public_unapproved_apps_db(db: Session, uid: str) -> List[Dict[str, Any]]:
    """Get public unapproved apps for a specific user."""
    apps = db.query(AppModel).filter(
        and_(
            AppModel.approved == False,
            AppModel.uid == uid,
            AppModel.private == False
        )
    ).all()
    return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]

@db_session_manager
def set_app_popular_db(db: Session, app_id: str, popular: bool):
    app = db.query(AppModel).filter(AppModel.id == app_id).first()
    if app:
        app.is_popular = popular
        db.flush()

@db_session_manager
def change_app_approval_status(db: Session, app_id: str, approved: bool) -> bool:
    app = db.query(AppModel).filter(AppModel.id == app_id).first()
    if app:
        app.approved = approved
        app.status = 'approved' if approved else 'rejected'
        db.flush()
        return True
    return False

@db_session_manager
def update_app_visibility_in_db(db: Session, app_id: str, private: bool):
    app = db.query(AppModel).filter(AppModel.id == app_id).first()
    if app:
        app.private = private
        db.flush()

@db_session_manager
def migrate_app_owner_id_db(db: Session, new_id: str, old_id: str):
    """Migrate app ownership from old_id to new_id."""
    apps = db.query(AppModel).filter(AppModel.uid == old_id).all()
    for app in apps:
        app.uid = new_id
    db.flush()
    logging.info(f"Migrated {len(apps)} apps from {old_id} to {new_id}")

# ********************************
# *********** REVIEWS ************
# ********************************

@db_session_manager
def set_app_review_in_db(db: Session, app_id: str, uid: str, review: Dict[str, Any]) -> bool:
    app = db.query(AppModel).filter(AppModel.id == app_id).first()
    if app:
        if app.reviews is None:
            app.reviews = []
        
        # Remove existing review from same user
        app.reviews = [r for r in app.reviews if r.get('uid') != uid]
        app.reviews.append(review)
        
        flag_modified(app, "reviews")
        db.flush()
        return True
    return False

# ********************************
# ************ TESTER ************
# ********************************

@db_session_manager
def add_tester_db(db: Session, data: dict):
    tester = TesterModel(**data)
    db.add(tester)
    db.flush()

@db_session_manager
def add_app_access_for_tester_db(db: Session, app_id: str, uid: str) -> None:
    tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
    if tester:
        if tester.apps is None:
            tester.apps = []
        if app_id not in tester.apps:
            tester.apps.append(app_id)
            flag_modified(tester, "apps")
            db.flush()
    else:
        new_tester = TesterModel(uid=uid, apps=[app_id])
        db.add(new_tester)
        db.flush()

@db_session_manager
def remove_app_access_for_tester_db(db: Session, app_id: str, uid: str) -> bool:
    tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
    if tester and tester.apps and app_id in tester.apps:
        tester.apps.remove(app_id)
        flag_modified(tester, "apps")
        db.flush()
        return True
    return False

@db_session_manager
def remove_tester_db(db: Session, uid: str) -> bool:
    tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
    if tester:
        db.delete(tester)
        db.flush()
        return True
    return False

@db_session_manager
def can_tester_access_app_db(db: Session, app_id: str, uid: str) -> bool:
    tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
    if tester and tester.apps:
        return app_id in tester.apps
    return False

@db_session_manager
def is_tester_db(db: Session, uid: str) -> bool:
    return db.query(TesterModel).filter(TesterModel.uid == uid).first() is not None

@db_session_manager
def get_apps_for_tester_db(db: Session, uid: str) -> List[Dict[str, Any]]:
    tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
    if tester and tester.apps:
        apps = db.query(AppModel).filter(
            and_(AppModel.approved == False, AppModel.id.in_(tester.apps))
        ).all()
        return [{c.name: getattr(app, c.name) for c in app.__table__.columns} for app in apps]
    return []

# ********************************
# *********** USAGE **************
# ********************************

@db_session_manager
def record_app_usage(
    db: Session, uid: str, app_id: str, usage_type: UsageHistoryType, 
    conversation_id: str = None, message_id: str = None, timestamp: datetime = None
) -> Dict[str, Any]:
    if not conversation_id and not message_id:
        raise ValueError('conversation_id or message_id must be provided')

    usage_data = {
        'uid': uid, 'app_id': app_id, 'usage_type': usage_type.value,
        'conversation_id': conversation_id, 'message_id': message_id,
        'timestamp': datetime.now(timezone.utc) if timestamp is None else timestamp,
    }
    new_usage = AppUsageHistoryModel(**usage_data)
    db.add(new_usage)
    db.flush()
    return {c.name: getattr(new_usage, c.name) for c in new_usage.__table__.columns}

@db_session_manager
def get_app_usage_history_db(db: Session, app_id: str) -> List[Dict[str, Any]]:
    usage = db.query(AppUsageHistoryModel).filter(AppUsageHistoryModel.app_id == app_id).all()
    return [{c.name: getattr(u, c.name) for c in u.__table__.columns} for u in usage]

@db_session_manager
def get_app_memory_created_integration_usage_count_db(db: Session, app_id: str) -> int:
    return db.query(AppUsageHistoryModel).filter(
        and_(
            AppUsageHistoryModel.app_id == app_id,
            AppUsageHistoryModel.usage_type == UsageHistoryType.memory_created_external_integration.value
        )
    ).count()

@db_session_manager
def get_app_memory_prompt_usage_count_db(db: Session, app_id: str) -> int:
    return db.query(AppUsageHistoryModel).filter(
        and_(
            AppUsageHistoryModel.app_id == app_id,
            AppUsageHistoryModel.usage_type == UsageHistoryType.memory_created_prompt.value
        )
    ).count()

@db_session_manager
def get_app_chat_message_sent_usage_count_db(db: Session, app_id: str) -> int:
    return db.query(AppUsageHistoryModel).filter(
        and_(
            AppUsageHistoryModel.app_id == app_id,
            AppUsageHistoryModel.usage_type == UsageHistoryType.chat_message_sent.value
        )
    ).count()

@db_session_manager
def get_app_usage_count_db(db: Session, app_id: str) -> int:
    return db.query(AppUsageHistoryModel).filter(AppUsageHistoryModel.app_id == app_id).count()

# ********************************
# *********** PERSONAS ***********
# ********************************

@db_session_manager
def delete_persona_db(db: Session, persona_id: str):
    persona = db.query(AppModel).filter(AppModel.id == persona_id).first()
    if persona:
        db.delete(persona)
        db.flush()

@db_session_manager
def get_personas_by_username_db(db: Session, username: str) -> List[Dict[str, Any]]:
    personas = db.query(AppModel).filter(AppModel.username == username).all()
    return [{**{c.name: getattr(p, c.name) for c in p.__table__.columns}, 'doc_id': p.id} for p in personas]

@db_session_manager
def get_persona_by_username_db(db: Session, username: str) -> Optional[Dict[str, Any]]:
    persona = db.query(AppModel).filter(
        and_(
            AppModel.username == username,
            AppModel.capabilities.op('@>')('"persona"')  # PostgreSQL array contains
        )
    ).first()
    if persona:
        return {c.name: getattr(persona, c.name) for c in persona.__table__.columns}
    return None

@db_session_manager
def get_persona_by_id_db(db: Session, persona_id: str) -> Optional[Dict[str, Any]]:
    persona = db.query(AppModel).filter(AppModel.id == persona_id).first()
    if persona:
        return {c.name: getattr(persona, c.name) for c in persona.__table__.columns}
    return None

@db_session_manager
def get_persona_by_uid_db(db: Session, uid: str) -> Optional[Dict[str, Any]]:
    persona = db.query(AppModel).filter(
        and_(
            AppModel.uid == uid,
            AppModel.capabilities.op('@>')('"persona"')
        )
    ).first()
    if persona:
        return {c.name: getattr(persona, c.name) for c in persona.__table__.columns}
    return None

@db_session_manager
def get_user_persona_by_uid(db: Session, uid: str) -> Optional[Dict[str, Any]]:
    persona = db.query(AppModel).filter(
        and_(
            AppModel.capabilities.op('@>')('"persona"'),
            AppModel.category == 'personality-emulation',
            AppModel.uid == uid
        )
    ).first()
    if persona:
        return {'id': persona.id, **{c.name: getattr(persona, c.name) for c in persona.__table__.columns}}
    return None

@db_session_manager
def create_user_persona_db(db: Session, persona_data: dict) -> Dict[str, Any]:
    """Create a new user persona in the database"""
    persona = AppModel(**persona_data)
    db.add(persona)
    db.flush()
    return persona_data

@db_session_manager
def get_persona_by_twitter_handle_db(db: Session, handle: str) -> Optional[Dict[str, Any]]:
    persona = db.query(AppModel).filter(
        and_(
            AppModel.category == 'personality-emulation',
            AppModel.twitter.op('->>')('username') == handle
        )
    ).first()
    if persona:
        return {'id': persona.id, **{c.name: getattr(persona, c.name) for c in persona.__table__.columns}}
    return None

@db_session_manager
def get_persona_by_username_twitter_handle_db(db: Session, username: str, handle: str) -> Optional[Dict[str, Any]]:
    persona = db.query(AppModel).filter(
        and_(
            AppModel.username == username,
            AppModel.category == 'personality-emulation',
            AppModel.twitter.op('->>')('username') == handle
        )
    ).first()
    if persona:
        return {'id': persona.id, **{c.name: getattr(persona, c.name) for c in persona.__table__.columns}}
    return None

@db_session_manager
def get_omi_personas_by_uid_db(db: Session, uid: str) -> List[Dict[str, Any]]:
    """Get Omi persona apps for a specific user."""
    personas = db.query(AppModel).filter(
        and_(
            AppModel.uid == uid,
            AppModel.capabilities.op('@>')('"persona"'),
            AppModel.connected_accounts.op('@>')('"omi"')  # Has 'omi' in connected_accounts
        )
    ).all()
    return [{c.name: getattr(p, c.name) for c in p.__table__.columns} for p in personas]

@db_session_manager
def get_omi_persona_apps_by_uid_db(db: Session, uid: str) -> List[Dict[str, Any]]:
    personas = db.query(AppModel).filter(
        and_(
            AppModel.uid == uid,
            AppModel.category == 'personality-emulation'
        )
    ).all()
    return [{c.name: getattr(p, c.name) for c in p.__table__.columns} for p in personas]

@db_session_manager
def add_persona_to_db(db: Session, persona_data: dict):
    persona = AppModel(**persona_data)
    db.add(persona)
    db.flush()

@db_session_manager
def update_persona_in_db(db: Session, persona_data: dict):
    persona = db.query(AppModel).filter(AppModel.id == persona_data['id']).first()
    if persona:
        for key, value in persona_data.items():
            if hasattr(persona, key):
                setattr(persona, key, value)
        db.flush()

# ********************************
# *********** API KEYS ***********
# ********************************

@db_session_manager
def create_api_key_db(db: Session, app_id: str, api_key_data: Dict[str, Any]) -> Dict[str, Any]:
    api_key = ApiKeyModel(app_id=app_id, **api_key_data)
    db.add(api_key)
    db.flush()
    return {c.name: getattr(api_key, c.name) for c in api_key.__table__.columns}

@db_session_manager
def get_api_key_by_id_db(db: Session, app_id: str, key_id: str) -> Optional[Dict[str, Any]]:
    api_key = db.query(ApiKeyModel).filter(
        and_(ApiKeyModel.app_id == app_id, ApiKeyModel.id == key_id)
    ).first()
    if api_key:
        return {c.name: getattr(api_key, c.name) for c in api_key.__table__.columns}
    return None

@db_session_manager
def get_api_key_by_hash_db(db: Session, app_id: str, hashed_key: str) -> Optional[Dict[str, Any]]:
    api_key = db.query(ApiKeyModel).filter(
        and_(ApiKeyModel.app_id == app_id, ApiKeyModel.hashed == hashed_key)
    ).first()
    if api_key:
        return {c.name: getattr(api_key, c.name) for c in api_key.__table__.columns}
    return None

@db_session_manager
def list_api_keys_db(db: Session, app_id: str) -> List[Dict[str, Any]]:
    keys = db.query(ApiKeyModel).filter(ApiKeyModel.app_id == app_id).order_by(desc(ApiKeyModel.created_at)).all()
    return [{k: v for k, v in {c.name: getattr(key, c.name) for c in key.__table__.columns}.items() 
             if k != 'hashed'} for key in keys]

@db_session_manager
def delete_api_key_db(db: Session, app_id: str, key_id: str) -> bool:
    key = db.query(ApiKeyModel).filter(
        and_(ApiKeyModel.app_id == app_id, ApiKeyModel.id == key_id)
    ).first()
    if key:
        db.delete(key)
        db.flush()
        return True
    return False