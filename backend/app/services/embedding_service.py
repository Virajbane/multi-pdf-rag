from typing import List
from langchain_ollama import OllamaEmbeddings
from loguru import logger

from app.config import settings

# Module-level singleton — we create this once and reuse it
# Creating a new OllamaEmbeddings object on every request would be wasteful
_embeddings_model = None


def get_embeddings_model() -> OllamaEmbeddings:
    """
    Return the singleton embeddings model.

    WHY singleton? The model object holds a connection to Ollama.
    Creating it once at startup means every request reuses the same
    connection — faster and more memory efficient.

    OllamaEmbeddings internally calls:
    POST http://localhost:11434/api/embeddings
    with {"model": "nomic-embed-text", "prompt": "your text here"}
    and returns a list of 768 floats.
    """
    global _embeddings_model

    if _embeddings_model is None:
        logger.info(
            f"Initializing embeddings model: {settings.OLLAMA_EMBED_MODEL}"
        )
        _embeddings_model = OllamaEmbeddings(
            model=settings.OLLAMA_EMBED_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
        )
        logger.success("Embeddings model ready")

    return _embeddings_model


def embed_query(text: str) -> List[float]:
    """
    Embed a single query string.
    Used during the QUERY phase — when user asks a question.
    Returns a list of 768 floats.
    """
    model = get_embeddings_model()
    vector = model.embed_query(text)
    logger.debug(f"Embedded query: '{text[:50]}...' → vector dim: {len(vector)}")
    return vector


def embed_documents(texts: List[str]) -> List[List[float]]:
    """
    Embed multiple documents in batch.
    More efficient than calling embed_query in a loop.
    Used internally by ChromaDB when storing chunks.
    """
    model = get_embeddings_model()
    vectors = model.embed_documents(texts)
    logger.debug(f"Embedded {len(texts)} documents")
    return vectors