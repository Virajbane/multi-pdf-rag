from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """
    All application settings loaded from .env file.
    Pydantic-settings automatically reads from environment variables
    and validates types. If a required variable is missing, it raises
    a clear error at startup — not buried in a runtime crash.
    """
    
    # Application
    APP_NAME: str = "Multi-PDF RAG Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Paths — using Path for cross-platform compatibility
    BASE_DIR: Path = Path(__file__).parent.parent  # points to /backend
    DATA_DIR: Path = BASE_DIR / "data"
    CHROMA_DIR: Path = DATA_DIR / "chroma_db"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    
    # Ollama — the local LLM server
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5"          # The chat model
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"  # The embedding model
    
    # RAG parameters — these directly affect answer quality
    CHUNK_SIZE: int = 1000       # Characters per chunk
    CHUNK_OVERLAP: int = 200     # Overlap between consecutive chunks
    RETRIEVAL_K: int = 5         # How many chunks to retrieve per query
    
    # ChromaDB
    CHROMA_COLLECTION_NAME: str = "pdf_documents"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Singleton — import this object everywhere
settings = Settings()

# Create required directories on startup
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)