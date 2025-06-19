# backend/database/postgres/conversations.py
import copy
import json
import zlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import desc, and_, or_, func

from database.helpers import prepare_for_write, prepare_for_read
from utils import encryption
from .client import get_db_session
from .models import Conversation as ConversationModel, ConversationPhoto as ConversationPhotoModel, PostprocessingResult as PostprocessingResultModel
from models.conversation import PostProcessingStatus, PostProcessingModel, ConversationStatus, ConversationPhoto
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
                compressed_bytes = bytes.fromhex(decrypted_payload)
                decompressed_json = zlib.decompress(compressed_bytes).decode('utf-8')
                data['transcript_segments'] = json.loads(decompressed_json)
            else:
                data['transcript_segments'] = json.loads(decrypted_payload)
        except (json.JSONDecodeError, TypeError, zlib.error, ValueError):
            # If decryption or decompression fails, it might be unencrypted data.
            # We can leave it as is, or try to parse it directly. For now, we pass.
            pass
    return data

def _prepare_conversation_for_write(data: Dict[str, Any], uid: str, level: str) -> Dict[str, Any]:
    data = copy.deepcopy(data)
    if 'transcript_segments' in data and isinstance(data['transcript_segments'], list):
        segments_json = json.dumps(data['transcript_segments'])
        compressed_segments_bytes = zlib.compress(segments_json.encode('utf-8'))
        data['transcript_segments_compressed'] = True
        payload_to_store = compressed_segments_bytes.hex()

        if level == 'enhanced':
            encrypted_segments = encryption.encrypt(payload_to_store, uid)
            data['transcript_segments'] = encrypted_segments
        else:
            # Store the hex representation of compressed bytes
            data['transcript_segments'] = payload_to_store
    return data

def _prepare_conversation_for_read(conversation_data: Optional[Dict[str, Any]], uid: str) -> Optional[Dict[str, Any]]:
    if not conversation_data:
        return None
    data = copy.deepcopy(conversation_data)
    level = data.get('data_protection_level')

    # Always try to decrypt if enhanced
    if level == 'enhanced':
        return _decrypt_conversation_data(data, uid)

    # Handle standard level with potential compression
    if data.get('transcript_segments_compressed'):
        if 'transcript_segments' in data and isinstance(data['transcript_segments'], str):
            try:
                # Data is stored as hex string of compressed bytes
                compressed_bytes = bytes.fromhex(data['transcript_segments'])
                decompressed_json = zlib.decompress(compressed_bytes).decode('utf-8')
                data['transcript_segments'] = json.loads(decompressed_json)
            except (json.JSONDecodeError, TypeError, zlib.error, ValueError):
                pass
    return data

# *****************************
# ********** CRUD *************
# *****************************

@prepare_for_write(data_arg_name='conversation_data', prepare_func=_prepare_conversation_for_write)
def upsert_conversation(uid: str, conversation_data: dict):
    db = get_db_session()
    try:
        # Filter out keys not in the model to prevent errors
        model_columns = {c.name for c in ConversationModel.__table__.columns}
        filtered_data = {k: v for k, v in conversation_data.items() if k in model_columns}
        
        conversation = ConversationModel(uid=uid, **filtered_data)
        db.merge(conversation) # Handles both insert and update
        db.commit()
    finally:
        db.close()

@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_conversation(uid: str, conversation_id: str):
    db = get_db_session()
    try:
        conversation = db.query(ConversationModel).filter(
            and_(ConversationModel.id == conversation_id, ConversationModel.uid == uid)
        ).first()
        if conversation:
            return {c.name: getattr(conversation, c.name) for c in conversation.__table__.columns}
        return None
    finally:
        db.close()

@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_conversations(uid: str, limit: int = 100, offset: int = 0, include_discarded: bool = False,
                      statuses: List[str] = [], start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None, categories: Optional[List[str]] = None):
    db = get_db_session()
    try:
        query = db.query(ConversationModel).filter(ConversationModel.uid == uid)
        if not include_discarded:
            query = query.filter(ConversationModel.discarded == False)
        if statuses:
            query = query.filter(ConversationModel.status.in_(statuses))
        if start_date:
            query = query.filter(ConversationModel.created_at >= start_date)
        if end_date:
            query = query.filter(ConversationModel.created_at <= end_date)
        if categories:
            # Assumes category is stored in the top-level 'category' column
            query = query.filter(ConversationModel.category.in_(categories))
        
        conversations = (
            query
            .order_by(desc(ConversationModel.created_at))
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [{c.name: getattr(conv, c.name) for c in conv.__table__.columns} for conv in conversations]
    finally:
        db.close()

@prepare_for_write(data_arg_name='update_data', prepare_func=_prepare_conversation_for_write)
def update_conversation(uid: str, conversation_id: str, update_data: dict):
    db = get_db_session()
    try:
        conversation = db.query(ConversationModel).filter(and_(ConversationModel.id == conversation_id, ConversationModel.uid == uid)).first()
        if conversation:
            for key, value in update_data.items():
                if hasattr(conversation, key):
                    setattr(conversation, key, value)
            db.commit()
            return True
        return False
    finally:
        db.close()

def update_conversation_title(uid: str, conversation_id: str, title: str):
    return update_conversation(uid, conversation_id, {'title': title})

def delete_conversation(uid: str, conversation_id: str):
    """Performs a hard delete of the conversation."""
    db = get_db_session()
    try:
        conversation = db.query(ConversationModel).filter(and_(ConversationModel.id == conversation_id, ConversationModel.uid == uid)).first()
        if conversation:
            db.delete(conversation)
            db.commit()
            return True
        return False
    finally:
        db.close()

@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_conversations_by_id(uid: str, conversation_ids: List[str]):
    if not conversation_ids:
        return []
    db = get_db_session()
    try:
        conversations = (
            db.query(ConversationModel)
            .filter(
                and_(
                    ConversationModel.uid == uid,
                    ConversationModel.id.in_(conversation_ids),
                    ConversationModel.discarded == False
                )
            )
            .all()
        )
        return [{c.name: getattr(conv, c.name) for c in conv.__table__.columns} for conv in conversations]
    finally:
        db.close()

# **************************************
# ********** STATUS & OTHER *************
# **************************************

@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_in_progress_conversation(uid: str):
    db = get_db_session()
    try:
        conversation = (
            db.query(ConversationModel)
            .filter(and_(ConversationModel.uid == uid, ConversationModel.status == 'in_progress', ConversationModel.discarded == False))
            .first()
        )
        if conversation:
            return {c.name: getattr(conversation, c.name) for c in conversation.__table__.columns}
        return None
    finally:
        db.close()

@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_processing_conversations(uid: str):
    return get_conversations(uid, statuses=['processing'])

def update_conversation_status(uid: str, conversation_id: str, status: str):
    return update_conversation(uid, conversation_id, {'status': status})

def set_conversation_as_discarded(uid: str, conversation_id: str):
    return update_conversation(uid, conversation_id, {'discarded': True})

def update_conversation_events(uid: str, conversation_id: str, events: List[dict]):
    return update_conversation(uid, conversation_id, {'events': events})

def update_conversation_action_items(uid: str, conversation_id: str, action_items: List[dict]):
    return update_conversation(uid, conversation_id, {'action_items': action_items})

def update_conversation_finished_at(uid: str, conversation_id: str, finished_at: datetime):
    return update_conversation(uid, conversation_id, {'finished_at': finished_at})

def update_conversation_segments(uid: str, conversation_id: str, segments: List[dict]):
    return update_conversation(uid, conversation_id, {'transcript_segments': segments})

def set_conversation_visibility(uid: str, conversation_id: str, visibility: str):
    return update_conversation(uid, conversation_id, {'visibility': visibility})

@prepare_for_read(decrypt_func=_prepare_conversation_for_read)
def get_last_completed_conversation(uid: str) -> Optional[dict]:
    db = get_db_session()
    try:
        conversation = (
            db.query(ConversationModel)
            .filter(and_(ConversationModel.uid == uid, ConversationModel.status == ConversationStatus.completed.value))
            .order_by(desc(ConversationModel.created_at))
            .first()
        )
        if conversation:
            return {c.name: getattr(conversation, c.name) for c in conversation.__table__.columns}
        return None
    finally:
        db.close()

# ****************************************
# ********** POSTPROCESSING **************
# ****************************************

def set_postprocessing_status(
        uid: str, conversation_id: str, status: PostProcessingStatus, fail_reason: str = None,
        model: PostProcessingModel = PostProcessingModel.fal_whisperx
):
    # This is better handled by updating the conversation's main status or a dedicated field.
    # For now, we'll update the `external_data` field to mirror Firestore's flexibility.
    db = get_db_session()
    try:
        conv = db.query(ConversationModel).filter(and_(ConversationModel.id == conversation_id, ConversationModel.uid == uid)).first()
        if conv:
            # Using mutable JSON support in SQLAlchemy
            if conv.external_data is None:
                conv.external_data = {}
            conv.external_data['postprocessing'] = {
                'status': status.value,
                'model': model.value,
                'fail_reason': fail_reason
            }
            # Mark the field as modified
            from sqlalchemy.orm.attributes import flag_modified
            flag_modified(conv, "external_data")
            db.commit()
    finally:
        db.close()

def store_model_segments_result(uid: str, conversation_id: str, model_name: str, segments: List[TranscriptSegment]):
    db = get_db_session()
    try:
        results = [
            PostprocessingResultModel(
                uid=uid, conversation_id=conversation_id, model_name=model_name,
                result_type='segment', data=segment.dict()
            ) for segment in segments
        ]
        db.add_all(results)
        db.commit()
    finally:
        db.close()

def store_model_emotion_predictions_result(
        uid: str, conversation_id: str, model_name: str,
        predictions: List[hume.HumeJobModelPredictionResponseModel]
):
    db = get_db_session()
    try:
        results = [
            PostprocessingResultModel(
                uid=uid, conversation_id=conversation_id, model_name=model_name,
                result_type='emotion',
                data={
                    "start": p.time[0], "end": p.time[1],
                    "emotions": json.dumps(hume.HumePredictionEmotionResponseModel.to_multi_dict(p.emotions))
                }
            ) for p in predictions
        ]
        db.add_all(results)
        db.commit()
    finally:
        db.close()

def get_conversation_transcripts_by_model(uid: str, conversation_id: str) -> Dict[str, List[Dict]]:
    db = get_db_session()
    try:
        results = db.query(PostprocessingResultModel).filter(
            and_(
                PostprocessingResultModel.uid == uid,
                PostprocessingResultModel.conversation_id == conversation_id,
                PostprocessingResultModel.result_type == 'segment'
            )
        ).all()
        
        transcripts = {
            'deepgram': [], 'soniox': [], 'speechmatics': [], 'whisperx': []
        }
        for res in results:
            model_key = res.model_name.replace('_streaming', '').replace('fal_', '')
            if model_key in transcripts:
                transcripts[model_key].append(res.data)
        
        # Sort each list by start time
        for key in transcripts:
            transcripts[key] = sorted(transcripts[key], key=lambda x: x.get('start', 0))
            
        return transcripts
    finally:
        db.close()

# ***********************************
# ********** OPENGLASS **************
# ***********************************

def store_conversation_photos(uid: str, conversation_id: str, photos: List[ConversationPhoto]):
    db = get_db_session()
    try:
        photo_models = [
            ConversationPhotoModel(
                uid=uid, conversation_id=conversation_id,
                url=p.url, timestamp=p.timestamp
            ) for p in photos
        ]
        db.add_all(photo_models)
        db.commit()
    finally:
        db.close()

def get_conversation_photos(uid: str, conversation_id: str) -> List[Dict]:
    db = get_db_session()
    try:
        photos = db.query(ConversationPhotoModel).filter(
            and_(ConversationPhotoModel.uid == uid, ConversationPhotoModel.conversation_id == conversation_id)
        ).all()
        return [{c.name: getattr(p, c.name) for c in p.__table__.columns} for p in photos]
    finally:
        db.close()