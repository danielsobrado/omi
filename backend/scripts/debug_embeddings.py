#!/usr/bin/env python3
"""
Debug script to trace where the OpenAI import error is coming from
"""

import os
import sys
import traceback

# Set environment before any imports
os.environ['EMBEDDING_PROVIDER'] = 'sentence-transformer'
os.environ['SENTENCE_TRANSFORMER_MODEL'] = 'sentence-transformers/all-MiniLM-L6-v2'

print("🔍 Starting debug trace...")
print(f"EMBEDDING_PROVIDER: {os.environ.get('EMBEDDING_PROVIDER')}")

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    print("1. Testing direct import of get_embedding_provider...")
    from utils.llm.clients import get_embedding_provider
    print(f"   ✅ Provider: {get_embedding_provider()}")
    
    print("2. Testing import of get_embeddings function...")
    from utils.llm.clients import get_embeddings
    print("   ✅ Function imported")
    
    print("3. Testing direct call to get_embeddings()...")
    embeddings_instance = get_embeddings()
    print(f"   ✅ Instance created: {type(embeddings_instance)}")
    
    print("4. Testing embedding generation...")
    result = embeddings_instance.embed_query("Hello world")
    print(f"   ✅ Embedding generated with {len(result)} dimensions")
    
except Exception as e:
    print(f"❌ Error at step: {e}")
    print("\n📋 Full traceback:")
    traceback.print_exc()
