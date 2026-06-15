import fitz  # PyMuPDF — imported as fitz (legacy name)
import uuid
from pathlib import Path
from typing import List, Tuple
from loguru import logger
from langchain_core.documents import Document

from app.config import settings


def load_pdf(file_path: Path, original_filename: str) -> Tuple[List[Document], str]:
    """
    Load a PDF file and extract text page by page.
    
    Returns:
        - List of LangChain Document objects (one per page)
        - file_id: unique identifier for this PDF
    
    WHY page-by-page? We preserve page numbers in metadata.
    This lets us cite "answer found on page 3" to the user.
    """
    
    file_id = str(uuid.uuid4())  # Unique ID for this document
    documents: List[Document] = []
    
    logger.info(f"Loading PDF: {original_filename} | file_id: {file_id}")
    
    try:
        # fitz.open() reads the PDF into memory
        # PyMuPDF is faster than pypdf and handles more edge cases
        pdf_document = fitz.open(str(file_path))
        
        total_pages = len(pdf_document)
        logger.info(f"PDF has {total_pages} pages")
        
        for page_num in range(total_pages):
            page = pdf_document[page_num]
            
            # get_text() extracts raw text. Other modes:
            # "html" → HTML with formatting
            # "dict" → structured dict with bounding boxes
            # "blocks" → text blocks with positions
            # We use plain text because we're doing semantic search, not layout
            text = page.get_text()
            
            # Skip empty pages (covers, blank pages)
            if not text.strip():
                logger.debug(f"Skipping empty page {page_num + 1}")
                continue
            
            # Create a LangChain Document
            # metadata is a free-form dict — attach whatever you need
            doc = Document(
                page_content=text,
                metadata={
                    "file_id": file_id,
                    "filename": original_filename,
                    "page": page_num + 1,      # 1-indexed (human-readable)
                    "total_pages": total_pages,
                    "source": str(file_path),  # LangChain convention: always include 'source'
                }
            )
            documents.append(doc)
        
        pdf_document.close()
        
        logger.success(f"Extracted {len(documents)} pages from {original_filename}")
        return documents, file_id
        
    except Exception as e:
        logger.error(f"Failed to load PDF {original_filename}: {e}")
        raise ValueError(f"Could not process PDF: {e}")


def get_pdf_info(file_path: Path) -> dict:
    """
    Extract basic metadata from a PDF without loading all content.
    Used for quick validation before full processing.
    """
    try:
        pdf = fitz.open(str(file_path))
        info = {
            "pages": len(pdf),
            "metadata": pdf.metadata,  # author, title, creator, etc.
            "is_encrypted": pdf.is_encrypted,
        }
        pdf.close()
        return info
    except Exception as e:
        raise ValueError(f"Cannot read PDF: {e}")