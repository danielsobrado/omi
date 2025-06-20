# backend/database/postgres/chat.py
import copy
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import desc, and_, func
from sqlalchemy.orm import Session

from database.helpers import prepare_for_write, prepare_for_read
from utils import encryption
from .client import db_session_manager
from .models import Message as MessageModel, File as FileModel, ChatSession as ChatSessionModel, Conversation as ConversationModel
from models.chat import Message

# --- ENCRYPTION HELPERS (same as before) ---
def _encrypt_chat_data(chat_data: Dict[str, Any], uid: str) -> Dict[str, Any]:
    data = copy.deepcopy(chat_data)
    if 'text' in data and isinstance(data['text'], str):
        data['text'] = encryption.encrypt(data['text'], uid)
    return data

def _decrypt_chat_data(chat_data: Dict[str, Any], uid: str) -> Dict[str, Any]:
    data = copy.deepcopy(chat_data)
    if 'text' in data and isinstance(data['text'], str):
        try:
            data['text'] = encryption.decrypt(data['text'], uid)
        except Exception:
            pass
    return data

def _prepare_data_for_write(data: Dict[str, Any], uid: str, level: str) -> Dict[str, Any]:
    if level == 'enhanced':
        return _encrypt_chat_data(data, uid)
    return data

def _prepare_message_for_read(message_data: Optional[Dict[str, Any]], uid: str) -> Optional[Dict[str, Any]]:
    if not message_data:
        return None
    level = message_data.get('data_protection_level')
    if level == 'enhanced':
        return _decrypt_chat_data(message_data, uid)
    return message_data
# --- END ENCRYPTION HELPERS ---

@db_session_manager
@prepare_for_write(data_arg_name='message_data', prepare_func=_prepare_data_for_write)
def save_message(db: Session, uid: str, message_data: dict) -> Dict[str, Any]:
    model_columns = {c.name for c in MessageModel.__table__.columns}
    filtered_data = {k: v for k, v in message_data.items() if k in model_columns}
    message = MessageModel(uid=uid, **filtered_data)
    db.add(message)
    db.flush()
    return {c.name: getattr(message, c.name) for c in message.__table__.columns}

def add_message(uid: str, message_data: dict):
    if 'memories' in message_data:
        del message_data['memories']
    return save_message(uid, message_data)

def add_app_message(text: str, app_id: str, uid: str, conversation_id: Optional[str] = None) -> Message:
    ai_message = Message(
        id=str(uuid.uuid4()), text=text, created_at=datetime.now(timezone.utc),
        sender='ai', app_id=app_id, from_external_integration=False, type='text',
        memories_id=[conversation_id] if conversation_id else [],
    )
    add_message(uid, ai_message.model_dump())
    return ai_message

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_message_for_read)
def get_messages(
    db: Session, uid: str, limit: int = 20, offset: int = 0, include_conversations: bool = False, 
    app_id: Optional[str] = None, chat_session_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    query = db.query(MessageModel).filter(and_(MessageModel.uid == uid, MessageModel.reported == False))
    if app_id:
        query = query.filter(MessageModel.app_id == app_id)
    if chat_session_id:
        query = query.filter(MessageModel.session_id == chat_session_id)

    messages_models = query.order_by(desc(MessageModel.created_at)).limit(limit).offset(offset).all()
    messages = [{c.name: getattr(msg, c.name) for c in msg.__table__.columns} for msg in messages_models]

    if not include_conversations or not messages:
        return messages

    conversation_ids = {cid for msg in messages if msg.get('memories_id') for cid in msg['memories_id']}
    file_ids = {fid for msg in messages if msg.get('files_id') for fid in msg['files_id']}

    conversation_map = {}
    if conversation_ids:
        convs = db.query(ConversationModel).filter(ConversationModel.id.in_(list(conversation_ids))).all()
        conversation_map = {c.id: {col.name: getattr(c, col.name) for col in c.__table__.columns} for c in convs}

    file_map = {}
    if file_ids:
        files = db.query(FileModel).filter(FileModel.id.in_(list(file_ids))).all()
        file_map = {f.id: {col.name: getattr(f, col.name) for col in f.__table__.columns} for f in files}

    for msg in messages:
        msg['memories'] = [conversation_map[cid] for cid in msg.get('memories_id', []) if cid in conversation_map]
        msg['files'] = [file_map[fid] for fid in msg.get('files_id', []) if fid in file_map]

    return messages

@db_session_manager
def clear_chat(db: Session, uid: str, app_id: Optional[str] = None, chat_session_id: Optional[str] = None) -> Dict[str, str]:
    query = db.query(MessageModel).filter(MessageModel.uid == uid)
    if app_id:
        query = query.filter(MessageModel.app_id == app_id)
    if chat_session_id:
        query = query.filter(MessageModel.session_id == chat_session_id)
    
    deleted_count = query.delete(synchronize_session=False)
    logging.info(f"Cleared {deleted_count} messages for user {uid}.")
    return {"message": f"Deleted {deleted_count} messages."}

@db_session_manager
def add_chat_session(db: Session, uid: str, chat_session_data: dict) -> Dict[str, Any]:
    session = ChatSessionModel(uid=uid, **chat_session_data)
    db.add(session)
    db.flush()
    return {c.name: getattr(session, c.name) for c in session.__table__.columns}

@db_session_manager
def get_chat_session(db: Session, uid: str, app_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    query = db.query(ChatSessionModel).filter(ChatSessionModel.uid == uid)
    if app_id:
        query = query.filter(ChatSessionModel.app_id == app_id)
    session = query.first()
    if session:
        return {c.name: getattr(session, c.name) for c in session.__table__.columns}
    return None