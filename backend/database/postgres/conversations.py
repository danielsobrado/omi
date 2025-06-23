# backend/database/postgres/conversations.py
import asyncio
import copy
import json
import uuid
import zlib
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy import desc, and_, or_, func
from sqlalchemy.orm import Session

from database.helpers import prepare_for_write, prepare_for_read, set_data_protection_level
from utils import encryption
from .client import db_session_manager
from .models import (
    Conversation as ConversationModel, 
    ConversationPhoto as ConversationPhotoModel, 
    PostprocessingResult as PostprocessingResultModel
)
from models.conversation import (
    ConversationPhoto, PostProcessingStatus, PostProcessingModel, ConversationStatus
)
from models.transcript_segment import TranscriptSegment
import utils.other.hume as hume

# *********************************
# ******* ENCRYPTION HELPERS ******
# *********************************

def _decrypt_conversation_data(conversation_data: Dict[str, Any], uid: str) -> Dict[str, Any]:
    data = copy.deepcopy(conversation_data)

    if 'transcript_segments' in data and isinstance(data['transcript_segments'], str):
        try:
            decrypted_payload = encryption.decrypt(data['transcript_segments'], uid)
            if data.get('transcript_segments_compressed'):
                # New format: encrypted(compressed(json))
                compressed_bytes = bytes.fromhex(decrypted_payload)
                decompressed_json = zlib.decompress(compressed_bytes).decode('utf-8')
                data['transcript_segments'] = json.loads(decompressed_json)
            else:
                # Old format: encrypted(json)
                data['transcript_segments'] = json.loads(decrypted_payload)
        except (json.JSONDecodeError, TypeError, zlib.error, ValueError):
            pass

    return data

def _prepare_conversation_for_write(data: Dict[str, Any], uid: str, level: str) -> Dict[str, Any]:
    data = copy.deepcopy(data)
    if 'transcript_segments' in data and isinstance(data['transcript_segments'], list):
        segments_json = json.dumps(data['transcript_segments'])
        compressed_segments_bytes = zlib.compress(segments_json.encode('utf-8'))
        data['transcript_segments_compressed'] = True

        if level == 'enhanced':
            encrypted_segments = encryption.encrypt(compressed_segments_bytes.hex(), uid)
            data['transcript_segments'] = encrypted_segments
        else:
            data['transcript_segments'] = compressed_segments_bytes
    return data

def _prepare_conversation_for_read(conversation_data: Optional[Dict[str, Any]], uid: str) -> Optional[Dict[str, Any]]:
    if not conversation_data:
        return None

    data = copy.deepcopy(conversation_data)
    level = data.get('data_protection_level')

    if level == 'enhanced':
        return _decrypt_conversation_data(data, uid)

    # Handle standard level with potential compression
    if data.get('transcript_segments_compressed'):
        if 'transcript_segments' in data and isinstance(data['transcript_segments'], bytes):
            try:
                decompressed_json = zlib.decompress(data['transcript_segments']).decode('utf-8')
                data['transcript_segments'] = json.loads(decompressed_json)
            except (json.JSONDecodeError, TypeError, zlib.error):
                pass

    return data

# *****************************
# ********** CRUD *************
# *****************************

@db_session_manager
@set_data_protection_level(data_arg_name='conversation_data')
@prepare_for_write(data_arg_name='conversation_data', prepare_func=_prepare_conversation_for_write)
def upsert_conversation(db: Session, uid: str, conversation_data: dict):
    # Remove fields not stored directly in conversation table
    if 'audio_base64_url' in conversation_data:
        del conversation_data['audio_base64_url']
    if 'photos' in conversation_data:
        del conversation_data['photos']

    model_columns = {c.name for c in ConversationModel.__table__.columns}
    filtered_data = {k: v for k, v in conversation_data.items() if k in model_columns}
    
    # Check if conversation exists
    existing = db.query(ConversationModel).filter(
        and_(ConversationModel.uid == uid, ConversationModel.id == filtered_data['id'])
    ).first()
    
    if existing:
        # Update existing
        for key, value in filtered_data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
    else:
        # Create new
        conversation = ConversationModel(uid=uid, **filtered_data)
        db.add(conversation)
    
    db.flush()

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_conversation(db: Session, uid: str, conversation_id: str):
    conversation = db.query(ConversationModel).filter(
        and_(ConversationModel.uid == uid, ConversationModel.id == conversation_id)
    ).first()
    
    if conversation:
        return {c.name: getattr(conversation, c.name) for c in conversation.__table__.columns}
    return None

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_conversations(
    db: Session, uid: str, limit: int = 100, offset: int = 0, include_discarded: bool = False,
    statuses: List[str] = [], start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None, categories: Optional[List[str]] = None
):
    query = db.query(ConversationModel).filter(ConversationModel.uid == uid)
    
    if not include_discarded:
        query = query.filter(or_(ConversationModel.discarded == False, ConversationModel.discarded.is_(None)))
    
    if statuses:
        query = query.filter(ConversationModel.status.in_(statuses))
    
    if categories:
        # Assuming category is stored in structured data as JSON
        for category in categories:
            query = query.filter(ConversationModel.structured.op('->>')('category') == category)
    
    if start_date:
        query = query.filter(ConversationModel.created_at >= start_date)
    
    if end_date:
        query = query.filter(ConversationModel.created_at <= end_date)
    
    conversations = (
        query.order_by(desc(ConversationModel.created_at))
        .limit(limit)
        .offset(offset)
        .all()
    )
    
    return [{c.name: getattr(conv, c.name) for c in conv.__table__.columns} for conv in conversations]

@db_session_manager
def update_conversation(db: Session, uid: str, conversation_id: str, update_data: dict):
    conversation = db.query(ConversationModel).filter(
        and_(ConversationModel.uid == uid, ConversationModel.id == conversation_id)
    ).first()
    
    if not conversation:
        return False
    
    # Get current protection level for encryption
    doc_level = getattr(conversation, 'data_protection_level', 'standard')
    prepared_data = _prepare_conversation_for_write(update_data, uid, doc_level)
    
    for key, value in prepared_data.items():
        if hasattr(conversation, key):
            setattr(conversation, key, value)
    
    db.flush()
    return True

def update_conversation_title(uid: str, conversation_id: str, title: str):
    return update_conversation(uid, conversation_id, {'title': title})

@db_session_manager
def delete_conversation(db: Session, uid: str, conversation_id: str):
    conversation = db.query(ConversationModel).filter(
        and_(ConversationModel.uid == uid, ConversationModel.id == conversation_id)
    ).first()
    
    if conversation:
        db.delete(conversation)
        db.flush()
        return True
    return False

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def filter_conversations_by_date(db: Session, uid: str, start_date: datetime, end_date: datetime):
    conversations = db.query(ConversationModel).filter(
        and_(
            ConversationModel.uid == uid,
            ConversationModel.created_at >= start_date,
            ConversationModel.created_at <= end_date,
            or_(ConversationModel.discarded == False, ConversationModel.discarded.is_(None))
        )
    ).order_by(desc(ConversationModel.created_at)).all()
    
    return [{c.name: getattr(conv, c.name) for c in conv.__table__.columns} for conv in conversations]

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_conversations_by_id(db: Session, uid: str, conversation_ids: List[str]):
    if not conversation_ids:
        return []
    
    conversations = db.query(ConversationModel).filter(
        and_(
            ConversationModel.uid == uid,
            ConversationModel.id.in_(conversation_ids),
            or_(ConversationModel.discarded == False, ConversationModel.discarded.is_(None))
        )
    ).all()
    
    return [{c.name: getattr(conv, c.name) for c in conv.__table__.columns} for conv in conversations]

# **************************************
# ********** STATUS *************
# **************************************

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_in_progress_conversation(db: Session, uid: str):
    conversation = db.query(ConversationModel).filter(
        and_(
            ConversationModel.uid == uid,
            ConversationModel.status == 'in_progress'
        )
    ).first()
    
    if conversation:
        return {c.name: getattr(conversation, c.name) for c in conversation.__table__.columns}
    return None

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_processing_conversations(db: Session, uid: str):
    conversations = db.query(ConversationModel).filter(
        and_(
            ConversationModel.uid == uid,
            ConversationModel.status == 'processing'
        )
    ).all()
    
    return [{c.name: getattr(conv, c.name) for c in conv.__table__.columns} for conv in conversations]

def update_conversation_status(uid: str, conversation_id: str, status: str):
    return update_conversation(uid, conversation_id, {'status': status})

def set_conversation_as_discarded(uid: str, conversation_id: str):
    return update_conversation(uid, conversation_id, {'discarded': True})

# *********************************
# ********** CALENDAR *************
# *********************************

def update_conversation_events(uid: str, conversation_id: str, events: List[dict]):
    # Store as JSON in structured field
    structured_update = {'events': events}
    return update_conversation(uid, conversation_id, {'structured': structured_update})

# *********************************
# ******** ACTION ITEMS ***********
# *********************************

def update_conversation_action_items(uid: str, conversation_id: str, action_items: List[dict]):
    structured_update = {'action_items': action_items}
    return update_conversation(uid, conversation_id, {'structured': structured_update})

# ******************************
# ********** OTHER *************
# ******************************

def update_conversation_finished_at(uid: str, conversation_id: str, finished_at: datetime):
    return update_conversation(uid, conversation_id, {'finished_at': finished_at})

def update_conversation_segments(uid: str, conversation_id: str, segments: List[dict]):
    return update_conversation(uid, conversation_id, {'transcript_segments': segments})

# ***********************************
# ********** VISIBILITY *************
# ***********************************

def set_conversation_visibility(uid: str, conversation_id: str, visibility: str):
    return update_conversation(uid, conversation_id, {'visibility': visibility})

@db_session_manager
async def _get_public_conversation(db: Session, uid: str, conversation_id: str):
    conversation = db.query(ConversationModel).filter(
        and_(
            ConversationModel.uid == uid,
            ConversationModel.id == conversation_id,
            ConversationModel.visibility == 'public'
        )
    ).first()
    
    if conversation:
        conversation_data = {c.name: getattr(conversation, c.name) for c in conversation.__table__.columns}
        return _prepare_conversation_for_read(conversation_data, uid)
    return None

async def _get_public_conversations(data: List[Tuple[str, str]]):
    # Note: This is a simplified implementation
    # In production, you'd want proper async database session management
    results = []
    for uid, conversation_id in data:
        try:
            # Create new session for each query in async context
            from .client import db_session_manager
            with db_session_manager() as db:
                conversation = await _get_public_conversation(db, uid, conversation_id)
                if conversation:
                    results.append(conversation)
        except Exception as e:
            logging.error(f"Error fetching public conversation {conversation_id}: {e}")
            continue
    return results

def run_get_public_conversations(data: List[Tuple[str, str]]):
    return asyncio.run(_get_public_conversations(data))

# ****************************************
# ********** POSTPROCESSING **************
# ****************************************

@db_session_manager
def set_postprocessing_status(
    db: Session, uid: str, conversation_id: str, status: PostProcessingStatus, 
    fail_reason: str = None, model: PostProcessingModel = PostProcessingModel.fal_whisperx
):
    conversation = db.query(ConversationModel).filter(
        and_(ConversationModel.uid == uid, ConversationModel.id == conversation_id)
    ).first()
    
    if conversation:
        postprocessing_data = {
            'status': status.value,
            'model': model.value,
            'fail_reason': fail_reason
        }
        
        # Update or create postprocessing field in structured data
        if conversation.structured:
            conversation.structured['postprocessing'] = postprocessing_data
        else:
            conversation.structured = {'postprocessing': postprocessing_data}
        
        # Mark as modified for SQLAlchemy
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(conversation, "structured")
        db.flush()

@db_session_manager
def store_model_segments_result(
    db: Session, uid: str, conversation_id: str, model_name: str, segments: List[TranscriptSegment]
):
    results = []
    for i, segment in enumerate(segments):
        result = PostprocessingResultModel(
            id=str(uuid.uuid4()),
            uid=uid,
            conversation_id=conversation_id,
            model_name=model_name,
            result_type='segment',
            data=segment.dict(),
            created_at=datetime.now(timezone.utc)
        )
        results.append(result)
        
        # Batch commit every 400 items
        if i > 0 and i % 400 == 0:
            db.add_all(results)
            db.commit()
            results = []
    
    # Commit remaining
    if results:
        db.add_all(results)
        db.commit()

@db_session_manager
def store_model_emotion_predictions_result(
    db: Session, uid: str, conversation_id: str, model_name: str,
    predictions: List[hume.HumeJobModelPredictionResponseModel]
):
    now = datetime.now(timezone.utc)
    results = []
    
    for count, prediction in enumerate(predictions):
        result = PostprocessingResultModel(
            id=str(uuid.uuid4()),
            uid=uid,
            conversation_id=conversation_id,
            model_name=model_name,
            result_type='emotion',
            data={
                "start": prediction.time[0],
                "end": prediction.time[1],
                "emotions": json.dumps(hume.HumePredictionEmotionResponseModel.to_multi_dict(prediction.emotions)),
            },
            created_at=now
        )
        results.append(result)
        
        # Batch commit every 100 items
        if count > 0 and count % 100 == 0:
            db.add_all(results)
            db.commit()
            results = []
    
    # Commit remaining
    if results:
        db.add_all(results)
        db.commit()

@db_session_manager
def get_conversation_transcripts_by_model(db: Session, uid: str, conversation_id: str):
    results = db.query(PostprocessingResultModel).filter(
        and_(
            PostprocessingResultModel.uid == uid,
            PostprocessingResultModel.conversation_id == conversation_id,
            PostprocessingResultModel.result_type == 'segment'
        )
    ).all()
    
    transcripts = {
        'deepgram': [],
        'soniox': [],
        'speechmatics': [],
        'whisperx': []
    }
    
    for result in results:
        model_key = result.model_name.replace('_streaming', '').replace('fal_', '')
        if model_key in transcripts:
            transcripts[model_key].append(result.data)
    
    # Sort by start time
    for key in transcripts:
        transcripts[key] = sorted(transcripts[key], key=lambda x: x.get('start', 0))
    
    return transcripts

# ***********************************
# ********** OPENGLASS **************
# ***********************************

@db_session_manager
def store_conversation_photos(db: Session, uid: str, conversation_id: str, photos: List[ConversationPhoto]):
    photo_models = []
    for photo in photos:
        photo_model = ConversationPhotoModel(
            id=str(uuid.uuid4()),
            uid=uid,
            conversation_id=conversation_id,
            url=photo.url,
            timestamp=photo.timestamp,
            created_at=datetime.now(timezone.utc)
        )
        photo_models.append(photo_model)
    
    db.add_all(photo_models)
    db.commit()

@db_session_manager
def get_conversation_photos(db: Session, uid: str, conversation_id: str):
    photos = db.query(ConversationPhotoModel).filter(
        and_(
            ConversationPhotoModel.uid == uid,
            ConversationPhotoModel.conversation_id == conversation_id
        )
    ).all()
    
    return [{c.name: getattr(photo, c.name) for c in photo.__table__.columns} for photo in photos]

# ********************************
# ********** SYNCING *************
# ********************************

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_closest_conversation_to_timestamps(
    db: Session, uid: str, start_timestamp: int, end_timestamp: int
) -> Optional[dict]:
    logging.info(f'get_closest_conversation_to_timestamps {start_timestamp} {end_timestamp}')
    
    start_threshold = datetime.utcfromtimestamp(start_timestamp) - timedelta(minutes=2)
    end_threshold = datetime.utcfromtimestamp(end_timestamp) + timedelta(minutes=2)
    
    logging.info(f'get_closest_conversation_to_timestamps {start_threshold} {end_threshold}')
    
    conversations = db.query(ConversationModel).filter(
        and_(
            ConversationModel.uid == uid,
            ConversationModel.finished_at >= start_threshold,
            ConversationModel.started_at <= end_threshold
        )
    ).order_by(desc(ConversationModel.created_at)).all()
    
    logging.info(f'get_closest_conversation_to_timestamps len(conversations) {len(conversations)}')
    
    if not conversations:
        return None
    
    conversations_data = [{c.name: getattr(conv, c.name) for c in conv.__table__.columns} for conv in conversations]
    
    logging.info('get_closest_conversation_to_timestamps found:')
    for conversation in conversations_data:
        logging.info(f"- {conversation['id']} {conversation['started_at']} {conversation['finished_at']}")
    
    # Find conversation with closest start or end timestamp
    closest_conversation = None
    min_diff = float('inf')
    
    for conversation in conversations_data:
        conversation_start_timestamp = conversation['started_at'].timestamp()
        conversation_end_timestamp = conversation['finished_at'].timestamp()
        diff1 = abs(conversation_start_timestamp - start_timestamp)
        diff2 = abs(conversation_end_timestamp - end_timestamp)
        
        if diff1 < min_diff or diff2 < min_diff:
            min_diff = min(diff1, diff2)
            closest_conversation = conversation
    
    if closest_conversation:
        logging.info(f"get_closest_conversation_to_timestamps closest_conversation: {closest_conversation['id']}")
    
    return closest_conversation

@db_session_manager
@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_last_completed_conversation(db: Session, uid: str) -> Optional[dict]:
    conversation = db.query(ConversationModel).filter(
        and_(
            ConversationModel.uid == uid,
            ConversationModel.status == ConversationStatus.completed.value
        )
    ).order_by(desc(ConversationModel.created_at)).first()
    
    if conversation:
        return {c.name: getattr(conversation, c.name) for c in conversation.__table__.columns}
    return None