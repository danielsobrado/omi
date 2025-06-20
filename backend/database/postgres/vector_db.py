# backend/database/postgres/vector_db.py
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import and_, text
from sqlalchemy.orm import Session

from .client import db_session_manager
from .models import VectorStore as VectorStoreModel
from models.conversation import Conversation
from utils.llm.clients import embeddings

@db_session_manager
def upsert_vector2(db: Session, uid: str, conversation: Conversation, vector: List[float], metadata: Dict[str, Any]) -> None:
    doc_id = f'{uid}-{conversation.id}'
    new_vector = VectorStoreModel(
        id=doc_id, uid=uid, conversation_id=conversation.id,
        embedding=vector, metadata=metadata, created_at=datetime.utcnow()
    )
    db.merge(new_vector)
    logging.info(f"Upserted vector for conversation {conversation.id}")

@db_session_manager
def update_vector_metadata(db: Session, uid: str, conversation_id: str, metadata: dict) -> bool:
    doc_id = f'{uid}-{conversation_id}'
    vector_record = db.query(VectorStoreModel).filter(VectorStoreModel.id == doc_id).first()
    if vector_record:
        vector_record.metadata = metadata
        logging.info(f"Updated vector metadata for conversation {conversation_id}")
        return True
    logging.warning(f"Vector not found for conversation {conversation_id}, cannot update metadata.")
    return False

@db_session_manager
def query_vectors(db: Session, query: str, uid: str, starts_at: int = None, ends_at: int = None, k: int = 5) -> List[str]:
    query_embedding = embeddings.embed_query(query)
    filters = [VectorStoreModel.uid == uid]
    if starts_at is not None:
        filters.append(VectorStoreModel.created_at >= datetime.fromtimestamp(starts_at))
    if ends_at is not None:
        filters.append(VectorStoreModel.created_at <= datetime.fromtimestamp(ends_at))
        
    results = (
        db.query(VectorStoreModel)
        .filter(and_(*filters))
        .order_by(VectorStoreModel.embedding.l2_distance(query_embedding))
        .limit(k).all()
    )
    return [res.conversation_id for res in results]

@db_session_manager
def query_vectors_by_metadata(
    db: Session, uid: str, vector: List[float], dates_filter: List[datetime], 
    people: List[str], topics: List[str], entities: List[str], dates: List[str], limit: int = 5
) -> List[str]:
    filters = [VectorStoreModel.uid == uid]
    if dates_filter and len(dates_filter) == 2:
        filters.append(VectorStoreModel.created_at.between(dates_filter[0], dates_filter[1]))
        
    # Note: This metadata query is complex. For advanced JSON querying, raw SQL or specific
    # SQLAlchemy dialects might be needed. This is a simplified version.
    # The `?|` operator checks for the existence of any key from a list in a JSON array.
    json_or_filters = []
    if people:
        json_or_filters.append(VectorStoreModel.metadata['people'].astext.cast(text).op('?|')(people))
    if topics:
        json_or_filters.append(VectorStoreModel.metadata['topics'].astext.cast(text).op('?|')(topics))
    if entities:
        json_or_filters.append(VectorStoreModel.metadata['entities'].astext.cast(text).op('?|')(entities))

    if json_or_filters:
        filters.append(or_(*json_or_filters))

    results = (
        db.query(VectorStoreModel)
        .filter(and_(*filters))
        .order_by(VectorStoreModel.embedding.l2_distance(vector))
        .limit(limit).all()
    )
    return [res.conversation_id for res in results]

@db_session_manager
def delete_vector(db: Session, conversation_id: str) -> int:
    deleted_count = db.query(VectorStoreModel).filter(
        VectorStoreModel.conversation_id == conversation_id
    ).delete(synchronize_session=False)
    if deleted_count > 0:
        logging.info(f"Deleted {deleted_count} vector(s) for conversation {conversation_id}")
    return deleted_count