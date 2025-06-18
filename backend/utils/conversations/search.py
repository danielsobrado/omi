import math
import os
from datetime import datetime
from typing import Dict

import typesense

# Only initialize client if Typesense credentials are provided
client = None
typesense_api_key = os.getenv('TYPESENSE_API_KEY')
typesense_host = os.getenv('TYPESENSE_HOST')
typesense_port = os.getenv('TYPESENSE_HOST_PORT')

if typesense_api_key and typesense_host and typesense_port:
    try:
        client = typesense.Client({
            'nodes': [{
                'host': typesense_host,
                'port': typesense_port,
                'protocol': 'https'
            }],
            'api_key': typesense_api_key,
            'connection_timeout_seconds': 2
        })
    except Exception as e:
        print(f"Warning: Failed to initialize Typesense client: {e}")
        client = None


def search_conversations(
        uid: str,
        query: str,
        page: int = 1,
        per_page: int = 10,
        include_discarded: bool = True,
        start_date: int = None,
        end_date: int = None,
) -> Dict:
    # If Typesense is not configured, return empty results
    if client is None:
        print("Warning: Typesense is not configured, returning empty search results")
        return {
            'items': [],
            'total_pages': 0,
            'current_page': page,
            'per_page': per_page
        }
    
    try:

        filter_by = f'userId:={uid}'
        if not include_discarded:
            filter_by = filter_by + ' && discarded:=false'

        # Add date range filters if provided
        if start_date is not None:
            filter_by = filter_by + f' && created_at:>={start_date}'
        if end_date is not None:
            filter_by = filter_by + f' && created_at:<={end_date}'

        search_parameters = {
            'q': query,
            'query_by': 'structured, transcript_segments',
            'filter_by': filter_by,
            'sort_by': 'created_at:desc',
            'per_page': per_page,
            'page': page,
        }

        results = client.collections['conversations'].documents.search(search_parameters)
        memories = []
        for item in results['hits']:
            item['document']['created_at'] = datetime.utcfromtimestamp(item['document']['created_at']).isoformat()
            item['document']['started_at'] = datetime.utcfromtimestamp(item['document']['started_at']).isoformat()
            item['document']['finished_at'] = datetime.utcfromtimestamp(item['document']['finished_at']).isoformat()
            memories.append(item['document'])
        return {
            'items': memories,
            'total_pages': math.ceil(results['found'] / per_page),
            'current_page': page,
            'per_page': per_page
        }
    except Exception as e:
        raise Exception(f"Failed to search conversations: {str(e)}")
