from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from loguru import logger

from app.config import settings
from app.services.embedding_service import get_embeddings_model


# ── Singleton ChromaDB client ─────────────────────────────────────────────────

_chroma_client: Optional[chromadb.ClientAPI] = None
_vector_store: Optional[Chroma] = None


def get_chroma_client() -> chromadb.ClientAPI:
    """
    Return persistent ChromaDB client.
    PersistentClient saves data to disk at CHROMA_DIR.
    Data survives server restarts — you don't re-embed on every startup.
    """
    global _chroma_client

    if _chroma_client is None:
        logger.info(f"Connecting to ChromaDB at: {settings.CHROMA_DIR}")
        _chroma_client = chromadb.PersistentClient(
            path=str(settings.CHROMA_DIR),
            settings=ChromaSettings(
                anonymized_telemetry=False,  # don't send usage data to Chroma
                allow_reset=True,            # allow wiping for development
            ),
        )
        logger.success("ChromaDB client connected")

    return _chroma_client


def get_vector_store() -> Chroma:
    """
    Return LangChain's Chroma wrapper.

    WHY use LangChain's wrapper instead of raw ChromaDB?
    LangChain's Chroma class:
    - Automatically handles embedding generation when you call add_documents()
    - Returns LangChain Document objects (not raw dicts) from searches
    - Integrates directly with LangChain retrievers in Phase 3

    The wrapper talks to our ChromaDB client under the hood.
    """
    global _vector_store

    if _vector_store is None:
        client = get_chroma_client()
        embeddings = get_embeddings_model()

        _vector_store = Chroma(
            client=client,
            collection_name=settings.CHROMA_COLLECTION_NAME,
            embedding_function=embeddings,
            # collection_metadata sets the distance metric
            # cosine similarity is standard for text embeddings
            collection_metadata={"hnsw:space": "cosine"},
        )
        logger.success(
            f"Vector store ready: collection='{settings.CHROMA_COLLECTION_NAME}'"
        )

    return _vector_store


# ── Public API ────────────────────────────────────────────────────────────────

async def add_documents(chunks: List[Document]) -> int:
    """
    Embed and store chunks in ChromaDB.

    Internally this:
    1. Calls embedding model on each chunk's page_content
    2. Stores (vector, text, metadata) in ChromaDB
    3. Returns number of chunks stored

    The LangChain Chroma wrapper handles step 1 automatically —
    you just pass Documents, it figures out the rest.
    """
    if not chunks:
        logger.warning("add_documents called with empty list")
        return 0

    store = get_vector_store()

    logger.info(f"Storing {len(chunks)} chunks in ChromaDB...")

    # Generate unique IDs for each chunk
    # ChromaDB requires unique string IDs — we use file_id + chunk_index
    ids = [
        f"{chunk.metadata['file_id']}_{chunk.metadata.get('chunk_index', i)}"
        for i, chunk in enumerate(chunks)
    ]

    # add_documents triggers embedding generation + storage
    # This is the SLOW step — each chunk makes an API call to Ollama
    # For a 50-page PDF with ~200 chunks, expect ~30-60 seconds
    store.add_documents(documents=chunks, ids=ids)

    logger.success(f"Stored {len(chunks)} chunks successfully")
    return len(chunks)


async def search_documents(
    query: str,
    k: int = 5,
    file_ids: Optional[List[str]] = None,
) -> List[Document]:
    """
    Semantic search: find the k most relevant chunks for a query.

    HOW it works:
    1. Embed the query string → vector
    2. Compute cosine similarity against all stored vectors
    3. Return top-k Documents with their metadata

    file_ids filter: if provided, only search within those PDFs.
    This lets users ask "search only in document X".
    """
    store = get_vector_store()

    # Build optional metadata filter
    # ChromaDB filter syntax uses $in, $eq, $and, $or operators
    where_filter = None
    if file_ids:
        if len(file_ids) == 1:
            where_filter = {"file_id": {"$eq": file_ids[0]}}
        else:
            where_filter = {"file_id": {"$in": file_ids}}

    logger.info(
        f"Searching: '{query[:60]}...' | k={k} | "
        f"filter={where_filter or 'none'}"
    )

    # similarity_search_with_score returns (Document, score) tuples
    # Score is cosine distance (0 = identical, 1 = completely different)
    # We convert to similarity (1 - distance) for easier reading
    results_with_scores = store.similarity_search_with_score(
        query=query,
        k=k,
        filter=where_filter,
    )

    # Attach score to metadata so we can display it in citations
    documents = []
    for doc, score in results_with_scores:
        doc.metadata["relevance_score"] = round(1 - score, 4)
        documents.append(doc)
        logger.debug(
            f"  Match: '{doc.page_content[:60]}...' "
            f"| page={doc.metadata.get('page')} "
            f"| score={doc.metadata['relevance_score']}"
        )

    logger.info(f"Retrieved {len(documents)} chunks")
    return documents


async def delete_documents(file_id: str) -> int:
    """
    Delete all chunks belonging to a specific file_id.
    Called when a user removes an uploaded PDF.
    """
    client = get_chroma_client()

    try:
        collection = client.get_collection(settings.CHROMA_COLLECTION_NAME)

        # Get all IDs for this file first (so we know how many we deleted)
        results = collection.get(
            where={"file_id": {"$eq": file_id}},
            include=[],  # we only need IDs, not content
        )

        count = len(results["ids"])
        if count == 0:
            logger.warning(f"No chunks found for file_id: {file_id}")
            return 0

        # Delete by IDs
        collection.delete(ids=results["ids"])
        logger.success(f"Deleted {count} chunks for file_id: {file_id}")
        return count

    except Exception as e:
        logger.error(f"Failed to delete file {file_id}: {e}")
        raise


async def get_collection_stats() -> dict:
    """
    Get stats about what's stored — useful for the /documents endpoint.
    """
    try:
        client = get_chroma_client()
        collection = client.get_collection(settings.CHROMA_COLLECTION_NAME)
        count = collection.count()

        return {
            "total_chunks": count,
            "collection_name": settings.CHROMA_COLLECTION_NAME,
            "persist_directory": str(settings.CHROMA_DIR),
        }
    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        return {"total_chunks": 0, "error": str(e)}