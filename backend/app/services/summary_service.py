from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from loguru import logger
from app.config import settings
from app.services.vector_store import search_documents
import json

def get_llm():
    return ChatOllama(
        model=settings.OLLAMA_MODEL,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.2,
    )

async def summarize_document(file_id: str, style: str = "concise") -> dict:
    """
    Retrieve all chunks from a file and summarize them.
    We search with a generic query to pull the most representative chunks.
    """
    logger.info(f"Summarizing file_id: {file_id} | style: {style}")

    # Pull broad chunks covering the whole document
    queries = [
        "main topic and overview",
        "key findings and conclusions",
        "important details and facts",
    ]

    all_chunks = []
    for q in queries:
        chunks = await search_documents(query=q, k=4, file_ids=[file_id])
        all_chunks.extend(chunks)

    # Deduplicate by content
    seen = set()
    unique_chunks = []
    for c in all_chunks:
        if c.page_content not in seen:
            seen.add(c.page_content)
            unique_chunks.append(c)

    if not unique_chunks:
        return {"summary": "No content found for this document.", "file_id": file_id}

    context = "\n\n---\n\n".join([
        f"[Page {c.metadata.get('page', '?')}]\n{c.page_content}"
        for c in unique_chunks
    ])

    style_instructions = {
        "concise": "Write a concise 3-5 sentence summary covering the main points.",
        "detailed": "Write a detailed summary with key sections, findings, and important details.",
        "bullet": "Write a bullet-point summary with 5-8 key takeaways. Use • for bullets.",
    }

    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a document summarization expert.
{style_instructions.get(style, style_instructions['concise'])}
Base your summary ONLY on the provided context."""),
        ("human", "Context:\n{context}\n\nGenerate the summary now."),
    ])

    chain = prompt | get_llm() | StrOutputParser()
    summary = await chain.ainvoke({"context": context})

    logger.success(f"Summary generated for {file_id}")
    return {
        "summary": summary,
        "file_id": file_id,
        "style": style,
        "chunks_used": len(unique_chunks),
    }


async def generate_mcqs(file_id: str, num_questions: int = 5, difficulty: str = "medium") -> dict:
    """
    Generate multiple choice questions from document content.
    Returns structured JSON with questions, options, answers, explanations.
    """
    logger.info(f"Generating {num_questions} MCQs for {file_id} | difficulty: {difficulty}")

    chunks = await search_documents(
        query="important concepts facts definitions examples",
        k=8,
        file_ids=[file_id],
    )

    if not chunks:
        return {"questions": [], "file_id": file_id}

    context = "\n\n".join([c.page_content for c in chunks])

    difficulty_guide = {
        "easy": "straightforward factual questions",
        "medium": "questions requiring understanding and application",
        "hard": "analytical questions requiring deep understanding and inference",
    }

    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert exam question creator.
Generate exactly {num_questions} MCQs based on the context.
Difficulty level: {difficulty} — {difficulty_guide}

CRITICAL: Respond with ONLY valid JSON, no other text.
Format:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": [
        {{"label": "A", "text": "Option A text"}},
        {{"label": "B", "text": "Option B text"}},
        {{"label": "C", "text": "Option C text"}},
        {{"label": "D", "text": "Option D text"}}
      ],
      "correct_answer": "A",
      "explanation": "Brief explanation of why A is correct"
    }}
  ]
}}"""),
        ("human", "Context:\n{context}\n\nGenerate {num_questions} MCQs now. Respond with JSON only."),
    ])

    chain = prompt | get_llm() | StrOutputParser()

    raw = await chain.ainvoke({
        "context": context,
        "num_questions": num_questions,
        "difficulty": difficulty,
        "difficulty_guide": difficulty_guide.get(difficulty, ""),
    })

    # Parse JSON response
    try:
        # Strip markdown code blocks if model added them
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```")[1]
            if clean.startswith("json"):
                clean = clean[4:]
        parsed = json.loads(clean.strip())
        questions = parsed.get("questions", [])
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {e}\nRaw: {raw[:200]}")
        questions = []

    logger.success(f"Generated {len(questions)} MCQs")
    return {
        "file_id": file_id,
        "questions": questions,
        "difficulty": difficulty,
    }