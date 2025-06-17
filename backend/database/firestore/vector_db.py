import os
import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import List

import chromadb
from chromadb.utils import embedding_functions

from models.conversation import Conversation
from utils.llm.clients import embeddings

# --- ChromaDB Client Initialization ---
# This creates a persistent client that stores data on disk in the specified path.
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_chroma_db')
client = chromadb.PersistentClient(path=db_path)

# Use the OpenAI embedding function provided by ChromaDB, configured with your key.
# This ensures compatibility if you ever need to embed directly within Chroma.
# For now, we will continue to use the LangChain client for consistency.
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=os.environ.get('OPENAI_API_KEY'),
    model_name="text-embedding-3-large"
)

# Get or create a collection. This is similar to a Pinecone index.
# We pass the embedding function for Chroma to know how to handle data,
# though we will provide embeddings manually.
collection = client.get_or_create_collection(
    name=os.getenv("CHROMA_COLLECTION_NAME", "omi_conversations"),
    embedding_function=openai_ef
)

def _get_data(uid: str, conversation_id: str, vector: List[float]):
    return {
        "id": f'{uid}-{conversation_id}',
        "values": vector,
        'metadata': {
            'uid': uid,
            'memory_id': conversation_id,
            'created_at': int(datetime.now(timezone.utc).timestamp()),
        }
    }

def _get_data_for_chroma(uid: str, conversation_id: str, vector: List[float], metadata: dict = None):
    """
    Prepares data in the format ChromaDB expects for upserting.
    Metadata values in ChromaDB must be strings, integers, floats, or booleans.
    """
    # Ensure all metadata values are of a supported type.
    if metadata is None:
        metadata = {}
    
    chroma_metadata = {k: v for k, v in metadata.items() if v is not None}
    chroma_metadata['uid'] = uid
    chroma_metadata['memory_id'] = conversation_id
    chroma_metadata['created_at'] = int(datetime.now(timezone.utc).timestamp())
    
    # Ensure created_at is an integer timestamp
    if 'created_at' in chroma_metadata and isinstance(chroma_metadata['created_at'], datetime):
         chroma_metadata['created_at'] = int(chroma_metadata['created_at'].timestamp())

    return {
        "id": f'{uid}-{conversation_id}',
        "embedding": vector,
        "metadata": chroma_metadata
    }

def upsert_vector(uid: str, conversation: Conversation, vector: List[float]):
    """Upserts a single vector into ChromaDB (legacy compatibility)."""
    metadata = {
        'uid': uid,
        'memory_id': conversation.id,
        'created_at': int(datetime.now(timezone.utc).timestamp()),
    }
    
    collection.upsert(
        ids=[f'{uid}-{conversation.id}'],
        embeddings=[vector],
        metadatas=[metadata]
    )
    print(f"ChromaDB: Upserted vector for conversation {conversation.id}")

def upsert_vector2(uid: str, conversation: Conversation, vector: List[float], metadata: dict):
    """Upserts a single vector into ChromaDB."""
    data = _get_data_for_chroma(uid, conversation.id, vector, metadata)
    collection.upsert(
        ids=[data['id']],
        embeddings=[data['embedding']],
        metadatas=[data['metadata']]
    )
    print(f"ChromaDB: Upserted vector for conversation {conversation.id}")

def update_vector_metadata(uid: str, conversation_id: str, metadata: dict):
    """
    Updates the metadata for an existing vector in ChromaDB.
    ChromaDB updates by re-upserting. This requires fetching the existing
    embedding first, as we don't want to re-calculate it.
    """
    doc_id = f'{uid}-{conversation_id}'
    
    # 1. Get the existing document to retrieve its embedding
    try:
        existing_doc = collection.get(ids=[doc_id], include=["embeddings"])
        
        if not existing_doc or not existing_doc.get('embeddings') or not existing_doc['embeddings']:
            print(f"ChromaDB: Cannot update metadata. Document {doc_id} not found.")
            return

        existing_embedding = existing_doc['embeddings'][0]
        
        # 2. Upsert with the existing embedding and new metadata
        data = _get_data_for_chroma(uid, conversation_id, existing_embedding, metadata)
        collection.upsert(
            ids=[data['id']],
            embeddings=[data['embedding']],
            metadatas=[data['metadata']]
        )
        print(f"ChromaDB: Updated metadata for conversation {conversation_id}")
    except Exception as e:
        print(f"ChromaDB: Error updating metadata for {conversation_id}: {e}")

def upsert_vectors(
        uid: str, vectors: List[List[float]], conversations: List[Conversation]
):
    """Upserts a batch of vectors."""
    ids = [f'{uid}-{conv.id}' for conv in conversations]
    metadatas = [{'uid': uid, 'memory_id': conv.id, 'created_at': int(conv.created_at.timestamp())} for conv in conversations]
    
    collection.upsert(
        ids=ids,
        embeddings=vectors,
        metadatas=metadatas
    )
    print(f'ChromaDB: Upserted {len(vectors)} vectors.')

def query_vectors(query: str, uid: str, starts_at: int = None, ends_at: int = None, k: int = 5) -> List[str]:
    filter_data = {'uid': uid}
    if starts_at is not None:
        filter_data['created_at'] = {'$gte': starts_at}
    if ends_at is not None:
        if 'created_at' not in filter_data:
            filter_data['created_at'] = {}
        filter_data['created_at']['$lte'] = ends_at

    # print('filter_data', filter_data)
    xq = embeddings.embed_query(query)
    
    results = collection.query(
        query_embeddings=[xq],
        n_results=k,
        where=filter_data,
        include=["metadatas"]
    )
    
    # Extract conversation IDs
    if results['ids'][0]:
        return [metadata['memory_id'] for metadata in results['metadatas'][0]]
    return []

def query_vectors_by_metadata(
        uid: str, vector: List[float], dates_filter: List[datetime], people: List[str], topics: List[str],
    entities: List[str], dates: List[str], limit: int = 5,
) -> List[str]:
    """
    Queries ChromaDB by metadata filters and a query vector.
    This function translates the Pinecone filter logic to ChromaDB's `where` clause.
    """
    where_filter = {"$and": [{'uid': {'$eq': uid}}]}

    # Build the structured data filter part ($or clause)
    structured_filters = []
    if people:
        structured_filters.append({'people': {'$in': people}})
    if topics:
        structured_filters.append({'topics': {'$in': topics}})
    if entities:
        structured_filters.append({'entities': {'$in': entities}})
    
    if structured_filters:
        where_filter["$and"].append({"$or": structured_filters})

    # Build the date filter part
    if dates_filter and len(dates_filter) == 2 and dates_filter[0] and dates_filter[1]:
        where_filter["$and"].append(
            {'created_at': {'$gte': int(dates_filter[0].timestamp()), '$lte': int(dates_filter[1].timestamp())}}
        )

    print('ChromaDB query_vectors_by_metadata where_filter:', json.dumps(where_filter))

    # Perform the query
    try:
        results = collection.query(
            query_embeddings=[vector],
            n_results=10000,  # Query a large number to filter down
            where=where_filter,
            include=["metadatas"]
        )
        
        # Fallback logic: If no results, retry without structured filters (people, topics, etc.)
        if not results['ids'][0] and len(where_filter['$and']) > 1:
            # Remove the structured filter part, which is the second element if it exists
            if any(key in where_filter['$and'][1].get('$or', [{}])[0] for key in ['people', 'topics', 'entities']):
                where_filter['$and'].pop(1)
                print('ChromaDB retrying without structured filters:', json.dumps(where_filter))
                results = collection.query(
                    query_embeddings=[vector],
                    n_results=20, # On fallback, just get the top N
                    where=where_filter,
                    include=["metadatas"]
                )

        if not results['ids'][0]:
            return []

        # ChromaDB doesn't have built-in scoring like the original Pinecone logic,
        # so we'll maintain the conversation_id_to_matches logic but simplify it
        conversation_id_to_matches = defaultdict(int)
        for metadata in results['metadatas'][0]:
            conversation_id = metadata['memory_id']
            for topic in topics:
                if topic in metadata.get('topics', []):
                    conversation_id_to_matches[conversation_id] += 1
            for entity in entities:
                if entity in metadata.get('entities', []):
                    conversation_id_to_matches[conversation_id] += 1
            for person in people:
                if person in metadata.get('people_mentioned', []):
                    conversation_id_to_matches[conversation_id] += 1

        # Extract conversation IDs
        conversations_id = [metadata['memory_id'] for metadata in results['metadatas'][0]]
        conversations_id.sort(key=lambda x: conversation_id_to_matches[x], reverse=True)
        
        print('ChromaDB query_vectors_by_metadata result:', conversations_id[:limit])
        return conversations_id[:limit]
    except Exception as e:
        print(f'ChromaDB query error: {e}')
        return []

def delete_vector(conversation_id: str):
    """Deletes vectors from ChromaDB by their conversation ID."""
    # We need to find the full document ID, which includes the UID.
    # This is less efficient than Pinecone's direct delete.
    # A better approach would be to pass the UID to this function.
    # For now, we query for it.
    try:
        results = collection.get(where={"memory_id": conversation_id}, include=[])
        if results['ids']:
            collection.delete(ids=results['ids'])
            print(f"ChromaDB: Deleted vector(s) for conversation {conversation_id}")
        else:
            print(f"ChromaDB: No vector found to delete for conversation {conversation_id}")
    except Exception as e:
        print(f"ChromaDB: Error deleting vector for {conversation_id}: {e}")
