from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from loguru import logger

from app.config import settings


def chunk_documents(documents: List[Document]) -> List[Document]:
    """
    Split a list of page-level Documents into smaller chunks.

    WHY chunk at all?
    - LLMs have context limits (~4K-32K tokens). A 200-page PDF won't fit.
    - Smaller chunks = more precise retrieval. If you retrieve a 10-page
      blob, 90% of it is irrelevant noise for the LLM to wade through.
    - Embeddings work best on short, focused text (< 512 tokens ideally).

    WHY overlap?
    - A sentence near the end of chunk 1 may be the KEY sentence for a query.
    - Without overlap, that sentence only lives in chunk 1. If chunk 2 is
      retrieved, the context is cut. With overlap = 200, that sentence
      appears in BOTH chunk 1 and chunk 2 — retrieval won't miss it.
    """

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,           # max chars per chunk
        chunk_overlap=settings.CHUNK_OVERLAP,     # overlap between chunks
        length_function=len,                       # use char count, not token count
        separators=[
            "\n\n",   # paragraph breaks — try this first
            "\n",     # line breaks
            ". ",     # sentence endings
            "? ",     # question endings
            "! ",     # exclamation endings
            " ",      # word boundaries
            "",       # last resort: split anywhere
        ],
        # Keep separator attached to the preceding chunk (more natural)
        keep_separator=True,
        # Add chunk index to metadata
        add_start_index=True,
    )

    # split_documents preserves and propagates metadata from parent docs
    # Each chunk inherits: file_id, filename, page, total_pages, source
    # It also adds: start_index (char position in original text)
    chunks = splitter.split_documents(documents)

    # Add chunk_index to each chunk's metadata so we can reference it later
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = i
        chunk.metadata["chunk_total"] = len(chunks)
        # Clean up text — remove excessive whitespace
        chunk.page_content = " ".join(chunk.page_content.split())

    # Filter out chunks that are too short to be useful
    # (e.g., a page that was just a header or page number)
    min_chunk_length = 50
    chunks = [c for c in chunks if len(c.page_content) >= min_chunk_length]

    logger.info(
        f"Chunked {len(documents)} pages → {len(chunks)} chunks "
        f"(size={settings.CHUNK_SIZE}, overlap={settings.CHUNK_OVERLAP})"
    )

    # Log a sample so you can verify quality in development
    if chunks and settings.DEBUG:
        sample = chunks[0]
        logger.debug(
            f"Sample chunk 0: '{sample.page_content[:100]}...' "
            f"| metadata: {sample.metadata}"
        )

    return chunks


def get_chunk_stats(chunks: List[Document]) -> dict:
    """
    Utility: get statistics about your chunks.
    Call this during development to tune chunk_size and overlap.
    """
    if not chunks:
        return {}

    lengths = [len(c.page_content) for c in chunks]
    return {
        "total_chunks": len(chunks),
        "avg_length": sum(lengths) / len(lengths),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "pages_covered": len(set(c.metadata.get("page", 0) for c in chunks)),
    }