# backend/database/postgres/chat.py
import copy
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import desc, and_, func, or_
from sqlalchemy.orm import Session

from database.helpers import prepare_for_write, prepare_for_read, set_data_protection_level
from utils import encryption
from .client import db_session_manager
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

@db_session_manager
@set_data_protection_level(data_arg_name='message_data')
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

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_message_for_read)
def get_app_messages(db: Session, uid: str, app_id: str, limit: int = 20, offset: int = 0, include_conversations: bool = False) -> List[Dict[str, Any]]:
    query = db.query(MessageModel).filter(
        and_(
            MessageModel.uid == uid,
            MessageModel.app_id == app_id,
            or_(MessageModel.reported == False, MessageModel.reported.is_(None))
        )
    )
    
    messages_models = query.order_by(desc(MessageModel.created_at)).limit(limit).offset(offset).all()
    messages = [{c.name: getattr(msg, c.name) for c in msg.__table__.columns} for msg in messages_models]

    if not include_conversations or not messages:
        return messages

    conversation_ids = {cid for msg in messages if msg.get('memories_id') for cid in msg['memories_id']}
    
    conversation_map = {}
    if conversation_ids:
        convs = db.query(ConversationModel).filter(ConversationModel.id.in_(list(conversation_ids))).all()
        conversation_map = {c.id: {col.name: getattr(c, col.name) for col in c.__table__.columns} for c in convs}

    for msg in messages:
        msg['memories'] = [conversation_map[cid] for cid in msg.get('memories_id', []) if cid in conversation_map]

    return messages

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_message_for_read)
def get_messages(
    db: Session, uid: str, limit: int = 20, offset: int = 0, include_conversations: bool = False, 
    app_id: Optional[str] = None, chat_session_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    logging.info(f'get_messages: uid={uid}, limit={limit}, offset={offset}, app_id={app_id}, include_conversations={include_conversations}')
    
    query = db.query(MessageModel).filter(
        and_(
            MessageModel.uid == uid,
            or_(MessageModel.reported == False, MessageModel.reported.is_(None))
        )
    )
    
    if app_id:
        query = query.filter(MessageModel.app_id == app_id)
    if chat_session_id:
        query = query.filter(MessageModel.chat_session_id == chat_session_id)

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
def get_message(db: Session, uid: str, message_id: str) -> tuple[Message, str] | None:
    message_model = db.query(MessageModel).filter(
        and_(MessageModel.uid == uid, MessageModel.id == message_id)
    ).first()
    
    if not message_model:
        return None

    message_data = {c.name: getattr(message_model, c.name) for c in message_model.__table__.columns}
    decrypted_data = _prepare_message_for_read(message_data, uid)
    message = Message(**decrypted_data)

    return message, str(message_model.id)

@db_session_manager
def report_message(db: Session, uid: str, msg_doc_id: str):
    try:
        message = db.query(MessageModel).filter(
            and_(MessageModel.uid == uid, MessageModel.id == msg_doc_id)
        ).first()
        
        if message:
            message.reported = True
            db.commit()
            return {"message": "Message reported"}
        else:
            return {"message": "Message not found"}
    except Exception as e:
        logging.error(f"Report message failed: {e}")
        db.rollback()
        return {"message": f"Update failed: {e}"}

@db_session_manager
def clear_chat(db: Session, uid: str, app_id: Optional[str] = None, chat_session_id: Optional[str] = None):
    try:
        query = db.query(MessageModel).filter(MessageModel.uid == uid)
        if app_id:
            query = query.filter(MessageModel.app_id == app_id)
        if chat_session_id:
            query = query.filter(MessageModel.chat_session_id == chat_session_id)
        
        deleted_count = query.delete(synchronize_session=False)
        db.commit()
        logging.info(f"Cleared {deleted_count} messages for user {uid}.")
        return None
    except Exception as e:
        db.rollback()
        return {"message": str(e)}

# *********************************
# ********* FILE HANDLING *********
# *********************************

@db_session_manager
def add_multi_files(db: Session, uid: str, files_data: list):
    try:
        for file_data in files_data:
            file_model = FileModel(uid=uid, **file_data)
            db.add(file_model)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to add files: {e}")
        raise

@db_session_manager
def get_chat_files(db: Session, uid: str, files_id: List[str] = []) -> List[Dict[str, Any]]:
    query = db.query(FileModel).filter(FileModel.uid == uid)
    
    if files_id:
        query = query.filter(FileModel.id.in_(files_id))
    
    files = query.all()
    return [{c.name: getattr(f, c.name) for c in f.__table__.columns} for f in files]

@db_session_manager
def delete_multi_files(db: Session, uid: str, files_data: list):
    try:
        file_ids = [file_data["id"] for file_data in files_data]
        db.query(FileModel).filter(
            and_(FileModel.uid == uid, FileModel.id.in_(file_ids))
        ).delete(synchronize_session=False)
        db.commit()
    except Exception as e:
        db.rollback()
        logging.error(f"Failed to delete files: {e}")
        raise

# *********************************
# ******* CHAT SESSIONS ***********
# *********************************

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

@db_session_manager
def delete_chat_session(db: Session, uid: str, chat_session_id: str):
    db.query(ChatSessionModel).filter(
        and_(ChatSessionModel.uid == uid, ChatSessionModel.id == chat_session_id)
    ).delete()
    db.commit()

@db_session_manager
def add_message_to_chat_session(db: Session, uid: str, chat_session_id: str, message_id: str):
    session = db.query(ChatSessionModel).filter(
        and_(ChatSessionModel.uid == uid, ChatSessionModel.id == chat_session_id)
    ).first()
    
    if session:
        current_message_ids = session.message_ids or []
        if message_id not in current_message_ids:
            current_message_ids.append(message_id)
            session.message_ids = current_message_ids
            db.commit()

@db_session_manager
def add_files_to_chat_session(db: Session, uid: str, chat_session_id: str, file_ids: List[str]):
    if not file_ids:
        return

    session = db.query(ChatSessionModel).filter(
        and_(ChatSessionModel.uid == uid, ChatSessionModel.id == chat_session_id)
    ).first()
    
    if session:
        current_file_ids = session.file_ids or []
        new_file_ids = [fid for fid in file_ids if fid not in current_file_ids]
        if new_file_ids:
            current_file_ids.extend(new_file_ids)
            session.file_ids = current_file_ids
            db.commit()

# **************************************
# ********* MIGRATION HELPERS **********
# **************************************

@db_session_manager
def get_chats_to_migrate(db: Session, uid: str, target_level: str) -> List[dict]:
    """
    Finds all chat messages that are not at the target protection level.
    """
    messages = db.query(MessageModel).filter(
        and_(
            MessageModel.uid == uid,
            or_(
                MessageModel.data_protection_level != target_level,
                MessageModel.data_protection_level.is_(None)
            )
        )
    ).all()

    return [{'id': str(msg.id), 'type': 'chat'} for msg in messages]

@db_session_manager
def migrate_chats_level_batch(db: Session, uid: str, message_doc_ids: List[str], target_level: str):
    """
    Migrates a batch of chat messages to the target protection level.
    """
    try:
        messages = db.query(MessageModel).filter(
            and_(
                MessageModel.uid == uid,
                MessageModel.id.in_(message_doc_ids)
            )
        ).all()

        for message in messages:
            current_level = message.data_protection_level or 'standard'
            
            if current_level == target_level:
                continue

            # Convert message to dict for processing
            message_data = {c.name: getattr(message, c.name) for c in message.__table__.columns}
            plain_data = _prepare_message_for_read(message_data, uid)
            plain_text = plain_data.get('text')
            
            migrated_text = plain_text
            if target_level == 'enhanced' and isinstance(plain_text, str):
                migrated_text = encryption.encrypt(plain_text, uid)

            message.data_protection_level = target_level
            message.text = migrated_text

        db.commit()
        logging.info(f"Successfully migrated {len(messages)} messages to {target_level} level")
        
    except Exception as e:
        db.rollback()
        logging.error(f"Migration failed: {e}")
        raise