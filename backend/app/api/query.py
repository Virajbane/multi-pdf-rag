import time
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from app.models import QueryRequest, QueryResponse, SourceDocument
from app.services.rag_service import answer_question, stream_answer

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        result = await answer_question(
            question=request.question,
            file_ids=request.file_ids,
            k=request.k or 5,
        )

        sources = [
            SourceDocument(
                content=s["content"],
                filename=s["filename"],
                page=s["page"],
                file_id=s["file_id"],
                relevance_score=s["relevance_score"],
            )
            for s in result["sources"]
        ]

        return QueryResponse(
            answer=result["answer"],
            sources=sources,
            question=request.question,
            processing_time_ms=result["processing_time_ms"],
        )

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def query_stream(request: QueryRequest):
    async def generate():
        try:
            async for token in stream_answer(
                question=request.question,
                file_ids=request.file_ids,
                k=request.k or 5,
            ):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: Error: {str(e)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )