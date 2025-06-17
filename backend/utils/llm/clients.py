import os
from typing import List, Union

from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
try:
    from langchain_huggingface import HuggingFaceEmbeddings
except ImportError:
    from langchain_community.embeddings import HuggingFaceEmbeddings
import tiktoken

from models.conversation import Structured

# Centralized OpenRouter configuration
openrouter_config = {
    "api_key": os.environ.get("OPENROUTER_API_KEY"),
    "base_url": "https://openrouter.ai/api/v1",
    "default_headers": {
        "HTTP-Referer": os.environ.get("OPENROUTER_REFERRER", "https://omi.me"),
        "X-Title": os.environ.get("OPENROUTER_TITLE", "Omi Chat"),
    }
}

# Filter out None values from the config, so it doesn't override defaults if an env var is not set
openrouter_config = {k: v for k, v in openrouter_config.items() if v is not None}

# Define models using OpenRouter identifiers
# Note: Model names like 'o1-preview' and 'o4-mini' have been mapped to their likely OpenRouter equivalents.
# You can adjust these to any model available on OpenRouter.
llm_mini = ChatOpenAI(model='openai/gpt-4o-mini', **openrouter_config)
llm_mini_stream = ChatOpenAI(model='openai/gpt-4o-mini', streaming=True, **openrouter_config)

llm_large = ChatOpenAI(model='openai/gpt-4o', **openrouter_config)
llm_large_stream = ChatOpenAI(model='openai/gpt-4o', streaming=True, temperature=1, **openrouter_config)

llm_high = ChatOpenAI(model='openai/gpt-4o-mini', **openrouter_config)
llm_high_stream = ChatOpenAI(model='openai/gpt-4o-mini', streaming=True, temperature=1, **openrouter_config)

llm_medium = ChatOpenAI(model='openai/gpt-4o', **openrouter_config)
llm_medium_experiment = ChatOpenAI(model='openai/gpt-4o', **openrouter_config)
llm_medium_stream = ChatOpenAI(model='openai/gpt-4o', streaming=True, **openrouter_config)

llm_persona_mini_stream = ChatOpenAI(
    temperature=0.8,
    model="google/gemini-flash-1.5",
    streaming=True,
    **openrouter_config
)
llm_persona_medium_stream = ChatOpenAI(
    temperature=0.8,
    model="anthropic/claude-3.5-sonnet",
    streaming=True,
    **openrouter_config
)

# Flexible embedding configuration
# Supports two embedding providers: 'openai' or 'sentence-transformer'

def get_embeddings():
    """
    Returns the configured embedding provider based on EMBEDDING_PROVIDER environment variable.
    
    Options:
    - 'openai': OpenAI embeddings (requires OPENAI_API_KEY)
    - 'sentence-transformer': Local Sentence Transformers (no API key needed)
    """
    EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "openai").lower()
    
    if EMBEDDING_PROVIDER == "openai":
        return OpenAIEmbeddings(
            model=os.environ.get("OPENAI_EMBEDDING_MODEL", "text-embedding-3-large"),
            api_key=os.environ.get("OPENAI_API_KEY")
        )
    elif EMBEDDING_PROVIDER == "sentence-transformer":
        # Using Qwen3-Embedding-8B as suggested, but you can change the model
        model_name = os.environ.get("SENTENCE_TRANSFORMER_MODEL", "Qwen/Qwen3-Embedding-8B")
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={
                # Use CPU by default, can be overridden with specific device
                # 'device': 'cuda' for GPU, 'cpu' for CPU
            },
            encode_kwargs={
                'normalize_embeddings': True,
                # For queries, you might want to add a prompt prefix
                # This can be configured per use case
            }
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {EMBEDDING_PROVIDER}. "
                        f"Supported options: 'openai', 'sentence-transformer'")

# Lazy initialization - get the provider name but don't initialize until first use
_embeddings = None

def get_embedding_provider():
    """Get the current embedding provider name."""
    return os.environ.get("EMBEDDING_PROVIDER", "openai").lower()

def get_embeddings_instance():
    """Get the embeddings instance (lazy-loaded)."""
    global _embeddings
    if _embeddings is None:
        _embeddings = get_embeddings()
    return _embeddings

# For backward compatibility, create a module-level embeddings object
class EmbeddingsWrapper:
    def __getattr__(self, name):
        return getattr(get_embeddings_instance(), name)
    
    def embed_query(self, text):
        return get_embeddings_instance().embed_query(text)
    
    def embed_documents(self, texts):
        return get_embeddings_instance().embed_documents(texts)

embeddings = EmbeddingsWrapper()

parser = PydanticOutputParser(pydantic_object=Structured)

encoding = tiktoken.encoding_for_model('gpt-4')


def num_tokens_from_string(string: str) -> int:
    """Returns the number of tokens in a text string."""
    num_tokens = len(encoding.encode(string))
    return num_tokens

def generate_embedding(content: str) -> List[float]:
    return embeddings.embed_documents([content])[0]
