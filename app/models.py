from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class DraftType(str, Enum):
    CASE_FACT_SUMMARY = "case_fact_summary"
    TITLE_REVIEW = "title_review"
    INTERNAL_MEMO = "internal_memo"
    DOCUMENT_CHECKLIST = "document_checklist"


class PatternType(str, Enum):
    TERMINOLOGY = "terminology"
    FORMATTING = "formatting"
    SECTION_ADDITION = "section_addition"
    SECTION_REMOVAL = "section_removal"


# =============================================================================
# DOCUMENT PROCESSING
# =============================================================================

class DocumentMetadata(BaseModel):
    filename: str
    page_count: int
    processed_at: datetime


class Chunk(BaseModel):
    chunk_id: str = Field(..., description="Unique chunk identifier")
    doc_id: str
    text: str
    page_number: int
    chunk_index: int
    char_count: int


class ProcessedDocument(BaseModel):
    doc_id: str
    filename: str
    raw_text: str
    chunks: List[Chunk]
    metadata: DocumentMetadata


# =============================================================================
# RETRIEVAL
# =============================================================================

class RetrievedChunk(BaseModel):
    chunk_id: str
    doc_id: str
    text: str
    page_number: int
    chunk_index: int
    score: float


class RetrievalResult(BaseModel):
    query: str
    retrieved_chunks: List[RetrievedChunk]
    total_retrieved: int
    retrieval_time_ms: float


# =============================================================================
# DRAFT GENERATION + GROUNDING
# =============================================================================

class EvidenceItem(BaseModel):
    claim: str
    source_chunk_id: str
    source_page: int
    supporting_text: str


class GeneratedDraft(BaseModel):
    doc_id: str
    draft_type: DraftType
    content: str
    evidence: List[EvidenceItem]
    generated_at: datetime
    model_used: str
    confidence_score: float


# =============================================================================
# FEEDBACK LEARNING
# =============================================================================

class OperatorEdit(BaseModel):
    doc_id: str
    draft_type: DraftType
    original_draft: str
    edited_draft: str
    edited_at: datetime


from pydantic import Field

class LearnedPattern(BaseModel):
    pattern_id: str
    pattern_type: PatternType
    description: str
    original_phrasing: str
    preferred_phrasing: str
    frequency: int = 1
    last_seen: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


# =============================================================================
# API REQUESTS
# =============================================================================

class ProcessRequest(BaseModel):
    filename: str


class DraftRequest(BaseModel):
    doc_id: str
    draft_type: DraftType = DraftType.CASE_FACT_SUMMARY


class FeedbackRequest(BaseModel):
    doc_id: str
    draft_type: DraftType
    original_draft: str
    edited_draft: str


# =============================================================================
# API RESPONSES
# =============================================================================

class ProcessResponse(BaseModel):
    success: bool
    doc_id: Optional[str] = None
    filename: Optional[str] = None
    chunk_count: Optional[int] = None
    page_count: Optional[int] = None
    error: Optional[str] = None


class DraftResponse(BaseModel):
    success: bool
    doc_id: str
    draft: Optional[GeneratedDraft] = None
    error: Optional[str] = None


class FeedbackResponse(BaseModel):
    success: bool
    patterns_extracted: int
    message: str


# =============================================================================
# STORAGE MODELS
# =============================================================================

class ProcessedDocumentRecord(BaseModel):
    """
    Stored in data/processed/*.json
    """
    doc_id: str
    filename: str
    metadata: Dict[str, Any]
    chunks: List[Chunk]


class LearnedPatternStore(BaseModel):
    patterns: List[LearnedPattern]