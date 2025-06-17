#!/usr/bin/env python3
"""
Test script for different embedding providers.
Run this to verify your embedding configuration is working correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Add the backend directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv('../.env')

def test_embeddings():
    """Test the configured embedding provider."""
    
    print("🧪 Testing Embedding Configuration")
    print("=" * 50)
    
    # Check environment variables
    provider = os.environ.get("EMBEDDING_PROVIDER", "openai")
    print(f"🔧 Environment EMBEDDING_PROVIDER: {provider}")
    
    try:
        from utils.llm.clients import embeddings, get_embedding_provider
        
        current_provider = get_embedding_provider()
        print(f"📊 Current provider: {current_provider}")
        
        # Try to get model info
        try:
            actual_embeddings = embeddings.get_embeddings() if hasattr(embeddings, 'get_embeddings') else embeddings
            model_info = getattr(actual_embeddings, 'model_name', getattr(actual_embeddings, 'model', 'N/A'))
            print(f"📈 Embedding model: {model_info}")
        except:
            print(f"📈 Embedding model: Using {current_provider} provider")
        
        # Test embedding generation
        test_texts = [
            "Hello, this is a test sentence.",
            "What is the capital of France?",
            "Machine learning is transforming technology."
        ]
        
        print("\n🔍 Testing embedding generation...")
        
        for i, text in enumerate(test_texts):
            print(f"  Text {i+1}: {text}")
            try:
                embedding = embeddings.embed_query(text)
                print(f"  ✅ Generated embedding with {len(embedding)} dimensions")
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                return False
        
        # Test batch embedding
        print(f"\n📦 Testing batch embedding...")
        try:
            batch_embeddings = embeddings.embed_documents(test_texts)
            print(f"  ✅ Generated {len(batch_embeddings)} embeddings")
            print(f"  📏 Dimensions: {len(batch_embeddings[0]) if batch_embeddings else 'N/A'}")
        except Exception as e:
            print(f"  ❌ Batch embedding error: {str(e)}")
            return False
            
        print(f"\n🎉 All tests passed! Your {current_provider} embedding setup is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize embedding provider: {str(e)}")
        print("\n💡 Troubleshooting tips:")
        print("  1. Check your .env file has the correct EMBEDDING_PROVIDER setting")
        print("  2. Verify you have the required API keys set")
        print("  3. For sentence-transformer, ensure you have enough disk space for model download")
        print("  4. Run: pip install -r requirements.txt")
        return False

def show_configuration_help():
    """Show help for configuring different embedding providers."""
    
    print("\n📋 Embedding Provider Configuration Guide")
    print("=" * 50)
    
    print("\n1️⃣  OPENAI (API-based, recommended)")
    print("   EMBEDDING_PROVIDER=openai")
    print("   OPENAI_API_KEY=your_openai_api_key")
    print("   OPENAI_EMBEDDING_MODEL=text-embedding-3-large")
    print("   📏 Dimensions: 1536 (or 3072 with higher dimension setting)")
    print("   💰 Cost: Pay per usage")
    print("   🌐 Get key: https://platform.openai.com/api-keys")
    
    print("\n2️⃣  SENTENCE-TRANSFORMER (Local, no API key)")
    print("   EMBEDDING_PROVIDER=sentence-transformer")
    print("   SENTENCE_TRANSFORMER_MODEL=Qwen/Qwen3-Embedding-8B")
    print("   📏 Dimensions: 4096 (Qwen3-8B) / varies by model")
    print("   💰 Cost: Free (local processing)")
    print("   💾 Storage: ~16GB for Qwen3-8B model")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        show_configuration_help()
    else:
        success = test_embeddings()
        if not success:
            show_configuration_help()
            sys.exit(1)
