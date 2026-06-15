from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from loguru import logger

from app.config import settings
from app.models import UploadResponse
from app.services.pdf_service import load_pdf, get_pdf_info
from app.services.chunking_service import chunk_documents
from app.services.vector_store import add_documents

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):

    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large. Max size: 50MB")

    temp_path = settings.UPLOAD_DIR / file.filename

    try:
        with open(temp_path, "wb") as f:
            f.write(content)

        logger.info(f"Saved uploaded file: {temp_path}")

        # Validate PDF
        pdf_info = get_pdf_info(temp_path)
        if pdf_info["is_encrypted"]:
            raise HTTPException(status_code=400, detail="Encrypted PDFs are not supported")

        # Load once
        documents, file_id = load_pdf(temp_path, file.filename)

        # Chunk → embed → store
        chunks = chunk_documents(documents)
        await add_documents(chunks)

        logger.success(f"Processed {file.filename}: {len(documents)} pages, {len(chunks)} chunks")

        return UploadResponse(
            file_id=file_id,
            filename=file.filename,
            pages=pdf_info["pages"],
            chunks_created=len(chunks),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    finally:
        if temp_path.exists():
            temp_path.unlink()
            logger.debug(f"Cleaned up temp file: {temp_path}")