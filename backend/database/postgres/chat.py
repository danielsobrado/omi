# backend/database/postgres/chat.py
import copy
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import desc, and_, func

from database.helpers import prepare_for_write, prepare_for_read
from utils import encryption
from .client import get_db_session
from .models import Message as MessageModel, File as FileModel, ChatSession as ChatSessionModel, Conversation as ConversationModel
from models.chat import Message

# *********************************
# ******* ENCRYPTION HELPERS ******
# *********************************

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

# *****************************
# ********** CRUD *************
# *****************************

@prepare_for_write(data_arg_name='message_data', prepare_func=_prepare_data_for_write)
def save_message(uid: str, message_data: dict):
    db = get_db_session()
    try:
        model_columns = {c.name for c in MessageModel.__table__.columns}
        filtered_data = {k: v for k, v in message_data.items() if k in model_columns}
        message = MessageModel(uid=uid, **filtered_data)
        db.add(message)
        db.commit()
        db.refresh(message)
        return {c.name: getattr(message, c.name) for c in message.__table__.columns}
    finally:
        db.close()

def add_message(uid: str, message_data: dict):
    # Firestore version deletes 'memories', but in PG we don't pass it in the first place.
    # The 'memories_id' array is what gets saved.
    if 'memories' in message_data:
        del message_data['memories']
    return save_message(uid, message_data)

def add_app_message(text: str, app_id: str, uid: str, conversation_id: Optional[str] = None) -> Message:
    ai_message = Message(
        id=str(uuid.uuid4()),
        text=text,
        created_at=datetime.now(timezone.utc),
        sender='ai',
        app_id=app_id,
        from_external_integration=False,
        type='text',
        memories_id=[conversation_id] if conversation_id else [],
    )
    add_message(uid, ai_message.model_dump())
    return ai_message

def add_summary_message(text: str, uid: str) -> Message:
    ai_message = Message(
        id=str(uuid.uuid4()),
        text=text,
        created_at=datetime.now(timezone.utc),
        sender='ai',
        app_id=None,
        from_external_integration=False,
        type='day_summary',
        memories_id=[],
    )
    add_message(uid, ai_message.model_dump())
    return ai_message

@prepare_for_read(decrypt_func=_prepare_message_for_read)
def get_messages(
        uid: str, limit: int = 20, offset: int = 0, include_conversations: bool = False, app_id: Optional[str] = None,
        chat_session_id: Optional[str] = None
):
    db = get_db_session()
    try:
        query = db.query(MessageModel).filter(and_(MessageModel.uid == uid, MessageModel.reported == False))
        if app_id:
            query = query.filter(MessageModel.app_id == app_id)
        if chat_session_id:
            query = query.filter(MessageModel.session_id == chat_session_id)

        messages_models = query.order_by(desc(MessageModel.created_at)).limit(limit).offset(offset).all()
        messages = [{c.name: getattr(msg, c.name) for c in msg.__table__.columns} for msg in messages_models]

        if not include_conversations or not messages:
            return messages

        # Collect all related IDs
        conversation_ids = set()
        file_ids = set()
        for msg in messages:
            if msg.get('memories_id'):
                conversation_ids.update(msg['memories_id'])
            if msg.get('files_id'):
                file_ids.update(msg['files_id'])

        # Batch fetch related conversations and files
        conversation_map = {}
        if conversation_ids:
            convs = db.query(ConversationModel).filter(ConversationModel.id.in_(list(conversation_ids))).all()
            conversation_map = {c.id: {col.name: getattr(c, col.name) for col in c.__table__.columns} for c in convs}

        file_map = {}
        if file_ids:
            files = db.query(FileModel).filter(FileModel.id.in_(list(file_ids))).all()
            file_map = {f.id: {col.name: getattr(f, col.name) for col in f.__table__.columns} for f in files}

        # Attach related data to messages
        for msg in messages:
            msg['memories'] = [conversation_map[cid] for cid in msg.get('memories_id', []) if cid in conversation_map]
            msg['files'] = [file_map[fid] for fid in msg.get('files_id', []) if fid in file_map]

        return messages
    finally:
        db.close()

@prepare_for_read(decrypt_func=_prepare_message_for_read)
def get_message(uid: str, message_id: str):
    db = get_db_session()
    try:
        message = db.query(MessageModel).filter(and_(MessageModel.id == message_id, MessageModel.uid == uid)).first()
        if message:
            return {c.name: getattr(message, c.name) for c in message.__table__.columns}
        return None
    finally:
        db.close()

def report_message(uid: str, message_id: str):
    db = get_db_session()
    try:
        message = db.query(MessageModel).filter(and_(MessageModel.id == message_id, MessageModel.uid == uid)).first()
        if message:
            message.reported = True
            db.commit()
            return {"message": "Message reported"}
        return {"message": "Message not found"}
    finally:
        db.close()

def clear_chat(uid: str, app_id: Optional[str] = None, chat_session_id: Optional[str] = None):
    db = get_db_session()
    try:
        query = db.query(MessageModel).filter(MessageModel.uid == uid)
        if app_id:
            query = query.filter(MessageModel.app_id == app_id)
        if chat_session_id:
            query = query.filter(MessageModel.session_id == chat_session_id)
        
        deleted_count = query.delete(synchronize_session=False)
        db.commit()
        return {"message": f"Deleted {deleted_count} messages."}
    except Exception as e:
        db.rollback()
        return {"message": str(e)}
    finally:
        db.close()

# ********************************
# ******* FILES & SESSIONS *******
# ********************************

def add_multi_files(uid: str, files_data: list):
    db = get_db_session()
    try:
        file_objects = [FileModel(uid=uid, **data) for data in files_data]
        db.add_all(file_objects)
        db.commit()
    finally:
        db.close()

def get_chat_files(uid: str, files_id: List[str] = []):
    db = get_db_session()
    try:
        query = db.query(FileModel).filter(FileModel.uid == uid)
        if files_id:
            query = query.filter(FileModel.id.in_(files_id))
        files = query.all()
        return [{c.name: getattr(f, c.name) for c in f.__table__.columns} for f in files]
    finally:
        db.close()

def delete_multi_files(uid: str, files_data: list):
    if not files_data:
        return
    db = get_db_session()
    try:
        ids_to_delete = [f['id'] for f in files_data]
        db.query(FileModel).filter(and_(FileModel.uid == uid, FileModel.id.in_(ids_to_delete))).delete(synchronize_session=False)
        db.commit()
    finally:
        db.close()

def add_chat_session(uid: str, chat_session_data: dict):
    db = get_db_session()
    try:
        session = ChatSessionModel(uid=uid, **chat_session_data)
        db.add(session)
        db.commit()
        db.refresh(session)
        return {c.name: getattr(session, c.name) for c in session.__table__.columns}
    finally:
        db.close()

def get_chat_session(uid: str, app_id: Optional[str] = None):
    db = get_db_session()
    try:
        query = db.query(ChatSessionModel).filter(ChatSessionModel.uid == uid)
        if app_id:
            query = query.filter(ChatSessionModel.app_id == app_id)
        session = query.first()
        if session:
            return {c.name: getattr(session, c.name) for c in session.__table__.columns}
        return None
    finally:
        db.close()

def delete_chat_session(uid: str, chat_session_id: str):
    db = get_db_session()
    try:
        session = db.query(ChatSessionModel).filter(and_(ChatSessionModel.id == chat_session_id, ChatSessionModel.uid == uid)).first()
        if session:
            db.delete(session)
            db.commit()
    finally:
        db.close()

def add_message_to_chat_session(uid: str, chat_session_id: str, message_id: str):
    db = get_db_session()
    try:
        session = db.query(ChatSessionModel).filter(and_(ChatSessionModel.id == chat_session_id, ChatSessionModel.uid == uid)).first()
        if session:
            session.message_ids = func.array_append(ChatSessionModel.message_ids, message_id)
            db.commit()
    finally:
        db.close()

def add_files_to_chat_session(uid: str, chat_session_id: str, file_ids: List[str]):
    if not file_ids:
        return
    db = get_db_session()
    try:
        session = db.query(ChatSessionModel).filter(and_(ChatSessionModel.id == chat_session_id, ChatSessionModel.uid == uid)).first()
        if session:
            session.file_ids = func.array_cat(ChatSessionModel.file_ids, file_ids)
            db.commit()
    finally:
        db.close()