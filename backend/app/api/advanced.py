from fastapi import APIRouter, HTTPException
from loguru import logger
from app.models import SummaryRequest, MCQRequest
from app.services.summary_service import summarize_document, generate_mcqs

router = APIRouter()

@router.post("/summarize")
async def summarize(request: SummaryRequest):
    try:
        result = await summarize_document(
            file_id=request.file_id,
            style=request.style,
        )
        return result
    except Exception as e:
        logger.error(f"Summarize failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mcq")
async def generate_mcq(request: MCQRequest):
    try:
        result = await generate_mcqs(
            file_id=request.file_id,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
        )
        return result
    except Exception as e:
        logger.error(f"MCQ generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))