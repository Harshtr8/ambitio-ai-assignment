from datetime import datetime
from hashlib import md5
from pathlib import Path
import logging

from app.models import (
    Chunk,
    DocumentMetadata,
    ProcessedDocument,
)
from app.processing.extractor import extract_document
from app.processing.cleaner import clean_document
from app.processing.chunker import chunk_document

logger = logging.getLogger(__name__)


# =============================================================================
# HELPERS
# =============================================================================

def generate_doc_id(filename: str) -> str:
    """
    Stable document identifier.

    Example:
    contract.pdf
    -> doc_a3f9b12c
    """

    hash_value = md5(
        filename.encode("utf-8")
    ).hexdigest()[:8]

    return f"doc_{hash_value}"


# =============================================================================
# PUBLIC PIPELINE
# =============================================================================

def process_document(
    file_path: Path,
) -> ProcessedDocument:
    """
    Full processing pipeline.

    PDF
      ↓
    extractor.py
      ↓
    cleaner.py
      ↓
    chunker.py
      ↓
    ProcessedDocument
    """

    logger.info(
        f"Processing started: {file_path.name}"
    )

    # -------------------------------------------------
    # 1. Extract
    # -------------------------------------------------

    extracted = extract_document(
        file_path
    )

    # -------------------------------------------------
    # 2. Clean
    # -------------------------------------------------

    cleaned = clean_document(
        extracted
    )

    # -------------------------------------------------
    # 3. Chunk
    # -------------------------------------------------

    chunks: list[Chunk] = chunk_document(
        cleaned
    )

    # -------------------------------------------------
    # 4. Build ProcessedDocument
    # -------------------------------------------------

    doc_id = generate_doc_id(
        file_path.name
    )

    metadata = DocumentMetadata(
        filename=file_path.name,
        page_count=cleaned["page_count"],
        processed_at=datetime.utcnow(),
    )

    document = ProcessedDocument(
        doc_id=doc_id,
        filename=file_path.name,
        raw_text=cleaned["raw_text"],
        chunks=chunks,
        metadata=metadata,
    )

    logger.info(
        f"Processing complete | "
        f"doc_id={doc_id} | "
        f"pages={metadata.page_count} | "
        f"chunks={len(chunks)}"
    )

    return document


__all__ = [
    "process_document",
]