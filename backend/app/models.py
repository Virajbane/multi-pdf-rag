from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# ─── Upload ──────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Returned after a PDF is successfully processed."""
    file_id: str                    # Unique identifier for this PDF
    filename: str
    pages: int                      # Total pages extracted
    chunks_created: int             # How many chunks were stored
    message: str = "Upload successful"

# ─── Query ───────────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """What the frontend sends when user asks a question."""
    question: str = Field(..., min_length=3, max_length=2000)
    file_ids: Optional[List[str]] = None  # None = search all PDFs
    k: Optional[int] = Field(default=5, ge=1, le=20)  # chunks to retrieve

class SourceDocument(BaseModel):
    """A single retrieved chunk with its metadata."""
    content: str                    # The actual text chunk
    filename: str
    page: int
    file_id: str
    relevance_score: Optional[float] = None  # cosine similarity score

class QueryResponse(BaseModel):
    """Full response sent back to frontend."""
    answer: str
    sources: List[SourceDocument]
    question: str
    processing_time_ms: int

# ─── Documents ───────────────────────────────────────────────────────────────

class DocumentInfo(BaseModel):
    """Metadata about an uploaded PDF."""
    file_id: str
    filename: str
    pages: int
    chunks: int
    uploaded_at: datetime
    size_bytes: int

# ─── Advanced Features ───────────────────────────────────────────────────────

class SummaryRequest(BaseModel):
    file_id: str
    style: str = Field(default="concise", pattern="^(concise|detailed|bullet)$")

class MCQRequest(BaseModel):
    file_id: str
    num_questions: int = Field(default=5, ge=1, le=20)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")

class MCQOption(BaseModel):
    label: str   # A, B, C, D
    text: str

class MCQQuestion(BaseModel):
    question: str
    options: List[MCQOption]
    correct_answer: str
    explanation: str

class MCQResponse(BaseModel):
    file_id: str
    questions: List[MCQQuestion]