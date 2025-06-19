# backend/database/postgres/vector_db.py
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy import and_, text
from sqlalchemy.dialects.postgresql import JSONB

from .client import get_db_session
from .models import VectorStore as VectorStoreModel
from models.conversation import Conversation
from utils.llm.clients import embeddings


def upsert_vector2(uid: str, conversation: Conversation, vector: List[float], metadata: Dict[str, Any]):
    """Upserts a single vector into the database."""
    db = get_db_session()
    try:
        doc_id = f'{uid}-{conversation.id}'
        
        # Check if vector exists
        existing_vector = db.query(VectorStoreModel).filter(VectorStoreModel.id == doc_id).first()
        
        if existing_vector:
            # Update
            existing_vector.embedding = vector
            existing_vector.metadata = metadata
            existing_vector.created_at = datetime.utcnow()
        else:
            # Insert
            new_vector = VectorStoreModel(
                id=doc_id,
                uid=uid,
                conversation_id=conversation.id,
                embedding=vector,
                metadata=metadata,
                created_at=datetime.utcnow()
            )
            db.add(new_vector)
        
        db.commit()
        print(f"PostgreSQL: Upserted vector for conversation {conversation.id}")
    finally:
        db.close()


def update_vector_metadata(uid: str, conversation_id: str, metadata: dict):
    """Updates the metadata for an existing vector in the database."""
    db = get_db_session()
    try:
        doc_id = f'{uid}-{conversation_id}'
        vector_record = db.query(VectorStoreModel).filter(VectorStoreModel.id == doc_id).first()
        if vector_record:
            vector_record.metadata = metadata
            db.commit()
            print(f"PostgreSQL: Updated metadata for conversation {conversation_id}")
        else:
            print(f"PostgreSQL: Vector not found for conversation {conversation_id}, cannot update metadata.")
    finally:
        db.close()


def query_vectors(query: str, uid: str, starts_at: int = None, ends_at: int = None, k: int = 5) -> List[str]:
    """Query vectors based on a text query and filters."""
    db = get_db_session()
    try:
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
            .limit(k)
            .all()
        )
        
        return [res.conversation_id for res in results]
    finally:
        db.close()


def query_vectors_by_metadata(
        uid: str, vector: List[float], dates_filter: List[datetime], people: List[str], topics: List[str],
    entities: List[str], dates: List[str], limit: int = 5,
) -> List[str]:
    """Queries vectors by metadata filters."""
    db = get_db_session()
    try:
        filters = [VectorStoreModel.uid == uid]
        
        if dates_filter and len(dates_filter) == 2:
            filters.append(VectorStoreModel.created_at.between(dates_filter[0], dates_filter[1]))
            
        # Build JSON contains query
        # Note: This assumes metadata is a flat dictionary. For nested objects, use -> or #> operators.
        # For arrays within JSON, use the `?|` operator.
        # Example: VectorStoreModel.metadata.op('?|')(people)
        json_filters = []
        if people:
            json_filters.append(text("metadata->'people' @> :people::jsonb").params(people=people))
        if topics:
            json_filters.append(text("metadata->'topics' @> :topics::jsonb").params(topics=topics))
        if entities:
            json_filters.append(text("metadata->'entities' @> :entities::jsonb").params(entities=entities))

        if json_filters:
            # This part is complex with OR logic. A raw text query might be simpler here.
            # For simplicity, we'll just AND them for now. A more complex query would use OR.
            filters.extend(json_filters)

        results = (
            db.query(VectorStoreModel)
            .filter(and_(*filters))
            .order_by(VectorStoreModel.embedding.l2_distance(vector))
            .limit(limit)
            .all()
        )
        return [res.conversation_id for res in results]
    finally:
        db.close()


def delete_vector(conversation_id: str):
    """Delete a vector from the database by conversation_id."""
    db = get_db_session()
    try:
        # This will delete all vectors associated with the conversation_id, regardless of user.
        deleted_count = db.query(VectorStoreModel).filter(VectorStoreModel.conversation_id == conversation_id).delete()
        db.commit()
        if deleted_count > 0:
            print(f"PostgreSQL: Deleted {deleted_count} vector(s) for conversation {conversation_id}")
        else:
            print(f"PostgreSQL: No vector found to delete for conversation {conversation_id}")
    finally:
        db.close()