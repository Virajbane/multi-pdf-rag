# Multi-PDF RAG Assistant

> Upload PDFs. Ask questions. Get cited answers — powered by local LLMs and semantic search.

![LangChain](https://img.shields.io/badge/LangChain-v0.3-purple)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal)
![Next.js](https://img.shields.io/badge/Next.js-14-black)
![ChromaDB](https://img.shields.io/badge/ChromaDB-local-orange)

## What it does

- Upload multiple PDFs via drag & drop
- Ask questions in natural language
- Get answers with **page-level source citations**
- Generate **summaries** and **MCQ quizzes** from any document
- 100% local — no OpenAI, no cloud costs

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| LLM | Qwen2.5:7b via Ollama | Free, local, no API costs |
| Embeddings | nomic-embed-text | Optimized for semantic search |
| Vector Store | ChromaDB | Persistent, no cloud needed |
| Orchestration | LangChain LCEL | Modern RAG pipeline |
| Backend | FastAPI + Python | Async, auto-docs at /docs |
| Frontend | Next.js 14 + TypeScript | App Router, dark UI |

## Architecture

```
INGESTION                          QUERY
─────────                          ─────
PDF Upload                         User Question
    ↓                                  ↓
PyMuPDF (extract text)             Embed question
    ↓                                  ↓
RecursiveCharacterTextSplitter     ChromaDB cosine search
    ↓                                  ↓
nomic-embed-text (vectors)         Top-5 chunks retrieved
    ↓                                  ↓
ChromaDB (store)                   Qwen2.5 generates answer
                                       ↓
                                   Cited response to UI
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- [Ollama](https://ollama.com/download)

### 1. Pull models
```bash
ollama serve
ollama pull qwen2.5:7b
ollama pull nomic-embed-text
```

### 2. Backend
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
python run.py
# API at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

### 4. Environment — create `backend/.env`
```
OLLAMA_MODEL=qwen2.5:7b
OLLAMA_EMBED_MODEL=nomic-embed-text:latest
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_K=5
```

## Features

- **RAG Q&A** — answers grounded in your documents, never hallucinated
- **Source citations** — every answer shows filename + page number + relevance score
- **PDF summarization** — concise, detailed, or bullet point styles
- **MCQ generation** — interactive quiz with easy/medium/hard difficulty
- **Multi-document search** — query across all uploaded PDFs simultaneously

## Project Structure

```
multi-pdf-rag/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routers
│   │   ├── services/     # PDF, chunking, embedding, RAG, vector store
│   │   ├── config.py     # Environment settings
│   │   └── models.py     # Pydantic schemas
│   └── run.py
└── frontend/
    ├── app/              # Next.js App Router
    ├── components/       # PDFUploader, ChatInterface, MCQQuiz
    └── lib/api.ts        # FastAPI client
```

## Author

**Viraj Bane**
