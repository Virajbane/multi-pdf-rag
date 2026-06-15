from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.config import settings

# Configure loguru — structured logging with colors in terminal
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="DEBUG" if settings.DEBUG else "INFO",
    colorize=True,
)
logger.add(
    "logs/app.log",   # Also write to file
    rotation="10 MB",
    retention="7 days",
    level="INFO",
)

# Create FastAPI instance
# title and version auto-populate the /docs UI
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production RAG system for multi-PDF question answering",
    docs_url="/docs",    # Swagger UI at http://localhost:8000/docs
    redoc_url="/redoc",  # ReDoc UI at http://localhost:8000/redoc
)

# CORS — required for Next.js (running on port 3000) to call this API (port 8000)
# Without this, browsers block cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # Next.js dev server
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
# We do this AFTER middleware setup
from app.api import upload, query, documents, advanced

app.include_router(upload.router, prefix="/api/v1", tags=["Upload"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])
app.include_router(documents.router, prefix="/api/v1", tags=["Documents"])
app.include_router(advanced.router, prefix="/api/v1", tags=["Advanced"])


@app.on_event("startup")
async def startup_event():
    """
    Runs when FastAPI starts. Good place to:
    - Warm up the LLM connection
    - Verify ChromaDB is accessible
    - Log configuration
    """
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Ollama: {settings.OLLAMA_BASE_URL} | Model: {settings.OLLAMA_MODEL}")
    logger.info(f"ChromaDB: {settings.CHROMA_DIR}")
    logger.info(f"Chunk size: {settings.CHUNK_SIZE} | Overlap: {settings.CHUNK_OVERLAP}")


@app.get("/health")
async def health_check():
    """Simple health check endpoint. Used by load balancers and monitoring."""
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {
        "message": "Multi-PDF RAG Assistant API",
        "docs": "/docs",
        "version": settings.APP_VERSION
    }