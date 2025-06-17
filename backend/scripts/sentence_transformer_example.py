#!/usr/bin/env python3
"""
Example of using Sentence Transformers directly for embeddings.
This shows the raw usage as mentioned in your request.

Note: This is for demonstration purposes. The actual Omi backend
uses the centralized embedding configuration in utils/llm/clients.py
"""

import os
from sentence_transformers import SentenceTransformer

def example_sentence_transformer_usage():
    """
    Example usage of Sentence Transformers as shown in your request.
    """
    
    print("🤖 Loading Sentence Transformer Model...")
    
    # Load the model (as shown in your example)
    # You can uncomment the advanced configuration if you have compatible hardware
    model = SentenceTransformer("Qwen/Qwen3-Embedding-8B")
    
    # Advanced configuration with flash attention (uncomment if supported):
    # model = SentenceTransformer(
    #     "Qwen/Qwen3-Embedding-8B",
    #     model_kwargs={"attn_implementation": "flash_attention_2", "device_map": "auto"},
    #     tokenizer_kwargs={"padding_side": "left"},
    # )
    
    print("✅ Model loaded successfully!")
    
    # The queries and documents to embed (from your example)
    queries = [
        "What is the capital of China?",
        "Explain gravity",
    ]
    documents = [
        "The capital of China is Beijing.",
        "Gravity is a force that attracts two bodies towards each other. It gives weight to physical objects and is responsible for the movement of planets around the sun.",
    ]
    
    print("\n🔍 Generating embeddings...")
    
    # Encode the queries and documents. Note that queries benefit from using a prompt
    # Here we use the prompt called "query" stored under `model.prompts`, but you can
    # also pass your own prompt via the `prompt` argument
    try:
        query_embeddings = model.encode(queries, prompt_name="query")
        print(f"📊 Query embeddings shape: {query_embeddings.shape}")
    except:
        # Fallback if "query" prompt is not available
        query_embeddings = model.encode(queries)
        print(f"📊 Query embeddings shape: {query_embeddings.shape}")
    
    document_embeddings = model.encode(documents)
    print(f"📄 Document embeddings shape: {document_embeddings.shape}")
    
    # Compute the (cosine) similarity between the query and document embeddings
    similarity = model.similarity(query_embeddings, document_embeddings)
    print(f"\n🎯 Similarity matrix:")
    print(similarity)
    
    # Expected output similar to:
    # tensor([[0.7493, 0.0751],
    #         [0.0880, 0.6318]])
    
    print(f"\n📈 Interpretation:")
    print(f"  Query 1 '{queries[0]}' is most similar to Document 1 (score: {similarity[0][0]:.4f})")
    print(f"  Query 2 '{queries[1]}' is most similar to Document 2 (score: {similarity[1][1]:.4f})")

def show_integration_info():
    """Show how this integrates with the Omi backend."""
    
    print("\n🔗 Integration with Omi Backend")
    print("=" * 40)
    print("To use Sentence Transformers in your Omi backend:")
    print("")
    print("1. Set in your .env file:")
    print("   EMBEDDING_PROVIDER=sentence-transformer")
    print("   SENTENCE_TRANSFORMER_MODEL=Qwen/Qwen3-Embedding-8B")
    print("")
    print("   OR for OpenAI:")
    print("   EMBEDDING_PROVIDER=openai")
    print("   OPENAI_API_KEY=your_openai_api_key")
    print("")
    print("2. The backend will automatically use HuggingFaceEmbeddings")
    print("   wrapper which internally uses sentence-transformers")
    print("")
    print("3. All existing code will work without changes!")
    print("   - embeddings.embed_query(text)")
    print("   - embeddings.embed_documents(texts)")
    print("")
    print("4. Benefits:")
    print("   ✅ No API calls - everything runs locally")
    print("   ✅ No API rate limits")
    print("   ✅ Better privacy (data stays local)")
    print("   ✅ Consistent performance")
    print("   ✅ Works offline")
    print("")
    print("5. Considerations:")
    print("   📦 Larger model download (~16GB for Qwen3-8B)")
    print("   💻 Higher memory usage")
    print("   ⚡ GPU recommended for faster inference")

if __name__ == "__main__":
    try:
        example_sentence_transformer_usage()
        show_integration_info()
    except ImportError:
        print("❌ sentence-transformers not installed.")
        print("💡 Install with: pip install sentence-transformers>=2.7.0")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("💡 Make sure you have enough disk space and memory for the model.")
