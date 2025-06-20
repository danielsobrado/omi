# backend/database/postgres/apps.py
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy import func, and_, or_
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from .client import db_session_manager
from .models import App as AppModel, Tester as TesterModel, AppUsageHistory as AppUsageHistoryModel, ApiKey as ApiKeyModel
from models.app import UsageHistoryType

@db_session_manager
def get_app_by_id_db(db: Session, app_id: str) -> Optional[Dict[str, Any]]:
    app = db.query(AppModel).filter(AppModel.id == app_id).first()
    if app:
        return {c.name: getattr(app, c.name) for c in app.__table__.columns}
    return None

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
def upsert_app_to_db(db: Session, app_data: Dict[str, Any]) -> None:
    db.merge(AppModel(**app_data))
    logging.info(f"Upserted app with ID: {app_data.get('id')}")

@db_session_manager
def update_app_in_db(db: Session, app_data: Dict[str, Any]) -> bool:
    app = db.query(AppModel).filter(AppModel.id == app_data['id']).first()
    if app:
        for key, value in app_data.items():
            if hasattr(app, key):
                setattr(app, key, value)
        logging.info(f"Updated app with ID: {app_data.get('id')}")
        return True
    return False

@db_session_manager
def delete_app_from_db(db: Session, app_id: str) -> bool:
    app = db.query(AppModel).filter(AppModel.id == app_id).first()
    if app:
        db.delete(app)
        logging.info(f"Deleted app with ID: {app_id}")
        return True
    return False

@db_session_manager
def change_app_approval_status(db: Session, app_id: str, approved: bool) -> bool:
    app = db.query(AppModel).filter(AppModel.id == app_id).first()
    if app:
        app.approved = approved
        app.status = 'approved' if approved else 'rejected'
        return True
    return False

@db_session_manager
def set_app_review_in_db(db: Session, app_id: str, uid: str, review: Dict[str, Any]) -> bool:
    app = db.query(AppModel).filter(AppModel.id == app_id).first()
    if app:
        if app.reviews is None:
            app.reviews = []
        
        app.reviews = [r for r in app.reviews if r.get('uid') != uid]
        app.reviews.append(review)
        
        flag_modified(app, "reviews")
        return True
    return False

@db_session_manager
def add_app_access_for_tester_db(db: Session, app_id: str, uid: str) -> None:
    tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
    if tester:
        if tester.apps is None:
            tester.apps = []
        if app_id not in tester.apps:
            tester.apps.append(app_id)
            flag_modified(tester, "apps")
    else:
        new_tester = TesterModel(uid=uid, apps=[app_id])
        db.add(new_tester)

@db_session_manager
def remove_app_access_for_tester_db(db: Session, app_id: str, uid: str) -> bool:
    tester = db.query(TesterModel).filter(TesterModel.uid == uid).first()
    if tester and tester.apps and app_id in tester.apps:
        tester.apps.remove(app_id)
        flag_modified(tester, "apps")
        return True
    return False

@db_session_manager
def is_tester_db(db: Session, uid: str) -> bool:
    return db.query(TesterModel).filter(TesterModel.uid == uid).first() is not None

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
def create_api_key_db(db: Session, app_id: str, api_key_data: Dict[str, Any]) -> Dict[str, Any]:
    api_key = ApiKeyModel(app_id=app_id, **api_key_data)
    db.add(api_key)
    db.flush()
    return {c.name: getattr(api_key, c.name) for c in api_key.__table__.columns}

@db_session_manager
def get_api_key_by_hash_db(db: Session, app_id: str, hashed_key: str) -> Optional[Dict[str, Any]]:
    api_key = db.query(ApiKeyModel).filter(and_(ApiKeyModel.app_id == app_id, ApiKeyModel.hashed == hashed_key)).first()
    if api_key:
        return {c.name: getattr(api_key, c.name) for c in api_key.__table__.columns}
    return None

@db_session_manager
def list_api_keys_db(db: Session, app_id: str) -> List[Dict[str, Any]]:
    keys = db.query(ApiKeyModel).filter(ApiKeyModel.app_id == app_id).order_by(desc(ApiKeyModel.created_at)).all()
    return [{k: v for k, v in key.__dict__.items() if k != 'hashed' and not k.startswith('_')} for key in keys]

@db_session_manager
def delete_api_key_db(db: Session, app_id: str, key_id: str) -> bool:
    key = db.query(ApiKeyModel).filter(and_(ApiKeyModel.app_id == app_id, ApiKeyModel.id == key_id)).first()
    if key:
        db.delete(key)
        return True
    return False