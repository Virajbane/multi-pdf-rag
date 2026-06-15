from typing import List, AsyncGenerator
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from loguru import logger
import time

from app.config import settings
from app.services.vector_store import search_documents


# ── LLM singleton ─────────────────────────────────────────────────────────────

_llm = None

def get_llm() -> ChatOllama:
    """
    Return singleton ChatOllama instance.

    ChatOllama talks to Ollama's chat API:
    POST http://localhost:11434/api/chat
    {"model": "qwen2.5", "messages": [...]}

    temperature=0.1 means nearly deterministic answers.
    0.0 = always same answer (good for factual RAG)
    1.0 = creative/random (bad for RAG — we want accuracy)
    """
    global _llm
    if _llm is None:
        logger.info(f"Initializing LLM: {settings.OLLAMA_MODEL}")
        _llm = ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.1,
        )
        logger.success("LLM ready")
    return _llm


# ── Prompt Template ───────────────────────────────────────────────────────────

# This is the most important part of RAG quality.
# The prompt tells the LLM:
# 1. Its role (helpful assistant)
# 2. The context (retrieved chunks)
# 3. The question
# 4. How to behave (cite sources, say "I don't know" if context is insufficient)

RAG_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful assistant that answers questions based on the provided document context.

RULES:
- Answer ONLY based on the context provided below
- If the context does not contain enough information, say "I cannot find this information in the uploaded documents"
- Always cite which page/document your answer comes from
- Be concise and accurate
- If asked to summarize, cover the key points from the context

CONTEXT FROM DOCUMENTS:
{context}
"""),
    ("human", "{question}"),
])


# ── Helper: format documents into context string ──────────────────────────────

def format_docs(docs: List[Document]) -> str:
    """
    Convert retrieved Document objects into a formatted string
    that gets injected into the prompt as {context}.

    WHY format this way?
    The LLM needs to know WHERE each piece of text came from
    so it can cite sources in its answer. We include filename
    and page number before each chunk.
    """
    formatted = []
    for i, doc in enumerate(docs):
        filename = doc.metadata.get("filename", "unknown")
        page = doc.metadata.get("page", "?")
        score = doc.metadata.get("relevance_score", 0)

        formatted.append(
            f"[Source {i+1}: {filename}, Page {page} (relevance: {score})]"
            f"\n{doc.page_content}"
        )

    return "\n\n---\n\n".join(formatted)


# ── Main RAG function ─────────────────────────────────────────────────────────

async def answer_question(
    question: str,
    file_ids: list = None,
    k: int = 5,
) -> dict:
    """
    Full RAG pipeline:
    1. Retrieve relevant chunks from ChromaDB
    2. Format them into context
    3. Build prompt (context + question)
    4. Send to Qwen2.5
    5. Return answer + source documents

    Returns a dict with 'answer' and 'sources'.
    """
    start_time = time.time()

    logger.info(f"RAG query: '{question[:80]}'")

    # ── Step 1: Retrieve ──────────────────────────────────────────────────────
    # Search ChromaDB for the most relevant chunks
    docs = await search_documents(
        query=question,
        k=k,
        file_ids=file_ids,
    )

    if not docs:
        return {
            "answer": "No relevant documents found. Please upload a PDF first.",
            "sources": [],
            "processing_time_ms": int((time.time() - start_time) * 1000),
        }

    # ── Step 2: Format context ────────────────────────────────────────────────
    context = format_docs(docs)
    logger.debug(f"Context length: {len(context)} chars from {len(docs)} chunks")

    # ── Step 3: Build the LCEL chain ─────────────────────────────────────────
    # This is the core of LangChain's modern API
    #
    # RunnablePassthrough() means "pass the input through unchanged"
    # The chain receives {"question": "...", "context": "..."}
    # and passes them to the prompt template
    #
    # Chain flow:
    # input_dict → RAG_PROMPT → ChatOllama → StrOutputParser → string

    llm = get_llm()
    output_parser = StrOutputParser()

    chain = RAG_PROMPT | llm | output_parser

    # ── Step 4: Invoke ────────────────────────────────────────────────────────
    logger.info("Sending to LLM...")

    answer = await chain.ainvoke({
        "context": context,
        "question": question,
    })

    processing_time = int((time.time() - start_time) * 1000)
    logger.success(f"Answer generated in {processing_time}ms")

    # ── Step 5: Build source citations ────────────────────────────────────────
    sources = []
    for doc in docs:
        sources.append({
            "content": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content,
            "filename": doc.metadata.get("filename", "unknown"),
            "page": doc.metadata.get("page", 0),
            "file_id": doc.metadata.get("file_id", ""),
            "relevance_score": doc.metadata.get("relevance_score", 0),
        })

    return {
        "answer": answer,
        "sources": sources,
        "processing_time_ms": processing_time,
    }


async def stream_answer(
    question: str,
    file_ids: list = None,
    k: int = 5,
) -> AsyncGenerator[str, None]:
    """
    Streaming version of answer_question.
    Yields text tokens as they are generated by Qwen2.5.
    This makes the frontend feel responsive — user sees
    words appearing in real time instead of waiting 30 seconds.
    """
    docs = await search_documents(query=question, k=k, file_ids=file_ids)

    if not docs:
        yield "No relevant documents found. Please upload a PDF first."
        return

    context = format_docs(docs)
    llm = get_llm()

    chain = RAG_PROMPT | llm | StrOutputParser()

    # astream() yields tokens as they arrive from Ollama
    async for token in chain.astream({
        "context": context,
        "question": question,
    }):
        yield token