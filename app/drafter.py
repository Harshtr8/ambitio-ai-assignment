import logging
from datetime import datetime, timezone
from typing import List

import google.generativeai as genai

from app.config import settings
from app.models import (
    DraftType,
    EvidenceItem,
    GeneratedDraft,
    RetrievedChunk,
)
from app.prompts import (
    BASE_SYSTEM_PROMPT,
    CASE_FACT_SUMMARY_PROMPT,
    DOCUMENT_CHECKLIST_PROMPT,
    INTERNAL_MEMO_PROMPT,
    TITLE_REVIEW_PROMPT,
)
from app.retriever import retrieve
from app.utils import load_learned_patterns

logger = logging.getLogger(__name__)


# =============================================================================
# GEMINI CONFIGURATION
# =============================================================================

genai.configure(
    api_key=settings.GEMINI_API_KEY
)


def _get_model():
    """
    Create Gemini model instance.
    """

    return genai.GenerativeModel(
        model_name=settings.MODEL_NAME,
        system_instruction=BASE_SYSTEM_PROMPT,
    )


# =============================================================================
# PUBLIC API
# =============================================================================

def generate_draft(
    doc_id: str,
    draft_type: DraftType,
) -> GeneratedDraft:
    """
    Generate a grounded legal draft.

    Flow:

    Retrieve
      ↓
    Evidence Block
      ↓
    Prompt
      ↓
    Gemini
      ↓
    GeneratedDraft
    """

    logger.info(
        f"Generating draft | "
        f"doc_id={doc_id} | "
        f"type={draft_type}"
    )

    query = _draft_type_to_query(
        draft_type
    )

    retrieval_result = retrieve(
        query=query,
        doc_id=doc_id,
        top_k=settings.TOP_K_CHUNKS,
    )

    if not retrieval_result.retrieved_chunks:

        logger.warning(
            f"No evidence retrieved "
            f"for doc_id={doc_id}"
        )

        return _empty_draft(
            doc_id,
            draft_type,
        )

    patterns = (
        load_learned_patterns()[-20:]
    )

    patterns_text = _format_patterns(
        patterns
    )

    evidence_block = (
        _build_evidence_block(
            retrieval_result.retrieved_chunks
        )
    )

    prompt = _build_prompt(
        draft_type=draft_type,
        evidence_block=evidence_block,
        learned_patterns=patterns_text,
        doc_id=doc_id,
    )

    content = _call_gemini(
        prompt
    )

    evidence = (
        _build_evidence_trail(
            retrieval_result.retrieved_chunks
        )
    )

    confidence_score = (
        _compute_confidence(
            retrieval_result.retrieved_chunks
        )
    )

    draft = GeneratedDraft(
        doc_id=doc_id,
        draft_type=draft_type,
        content=content,
        evidence=evidence,
        generated_at=datetime.now(
            timezone.utc
        ),
        model_used=settings.MODEL_NAME,
        confidence_score=confidence_score,
    )

    logger.info(
        f"Draft generated | "
        f"confidence={confidence_score}"
    )

    return draft


# =============================================================================
# QUERY GENERATION
# =============================================================================

def _draft_type_to_query(
    draft_type: DraftType,
) -> str:

    mapping = {
        DraftType.CASE_FACT_SUMMARY:
            (
                "parties involved "
                "facts timeline "
                "dates subject matter"
            ),

        DraftType.TITLE_REVIEW:
            (
                "property owner "
                "title chain "
                "encumbrances liens"
            ),

        DraftType.INTERNAL_MEMO:
            (
                "summary findings "
                "observations action items"
            ),

        DraftType.DOCUMENT_CHECKLIST:
            (
                "parties signatures "
                "references dates "
                "execution details"
            ),
    }

    return mapping.get(
        draft_type,
        "key document information",
    )


# =============================================================================
# EVIDENCE FORMATTING
# =============================================================================

def _build_evidence_block(
    chunks: List[RetrievedChunk],
) -> str:
    """
    Convert retrieved chunks
    into prompt-ready evidence.
    """

    sections = []

    for chunk in chunks:

        text = chunk.text[:800]

        sections.append(
            f"[{chunk.chunk_id} | "
            f"page {chunk.page_number} | "
            f"score={chunk.score}]\n"
            f"{text}\n"
            f"---"
        )

    return "\n\n".join(
        sections
    )


def _format_patterns(
    patterns: list,
) -> str:

    if not patterns:
        return (
            "No learned patterns."
        )

    lines = []

    for pattern in patterns:

        lines.append(
            f"- "
            f"[{pattern.get('pattern_type', 'general')}] "
            f"{pattern.get('description', '')}"
        )

    return "\n".join(lines)


# =============================================================================
# PROMPT SELECTION
# =============================================================================

def _build_prompt(
    draft_type: DraftType,
    evidence_block: str,
    learned_patterns: str,
    doc_id: str,
) -> str:

    current_date = (
        datetime.now(
            timezone.utc
        ).strftime("%Y-%m-%d")
    )

    prompt_map = {
        DraftType.CASE_FACT_SUMMARY:
            CASE_FACT_SUMMARY_PROMPT,

        DraftType.TITLE_REVIEW:
            TITLE_REVIEW_PROMPT,

        DraftType.INTERNAL_MEMO:
            INTERNAL_MEMO_PROMPT,

        DraftType.DOCUMENT_CHECKLIST:
            DOCUMENT_CHECKLIST_PROMPT,
    }

    template = prompt_map.get(
        draft_type,
        CASE_FACT_SUMMARY_PROMPT,
    )

    return template.format(
        evidence_block=evidence_block,
        learned_patterns=learned_patterns,
        doc_id=doc_id,
        current_date=current_date,
    )


# =============================================================================
# GEMINI CALL
# =============================================================================

def _call_gemini(
    prompt: str,
) -> str:

    try:

        model = _get_model()

        response = (
            model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,
                    max_output_tokens=(
                        settings.MAX_OUTPUT_TOKENS
                    ),
                ),
            )
        )

        try:

            text = (
                response.text.strip()
            )

            if text:
                return text

        except Exception:
            pass

        logger.warning(
            "Gemini returned empty content."
        )

        return (
            "[Draft generation failed "
            "- empty response]"
        )

    except Exception as e:

        logger.error(
            f"Gemini error: {e}"
        )

        return (
            f"[Draft generation failed: "
            f"{str(e)}]"
        )


# =============================================================================
# EVIDENCE TRAIL
# =============================================================================

def _build_evidence_trail(
    chunks: List[RetrievedChunk],
) -> List[EvidenceItem]:
    """
    Build inspectable evidence trail.
    """

    evidence = []

    for chunk in chunks:

        claim = (
            chunk.text[:120]
            .replace("\n", " ")
            .strip()
        )

        evidence.append(
            EvidenceItem(
                claim=claim,
                source_chunk_id=chunk.chunk_id,
                source_page=chunk.page_number,
                supporting_text=chunk.text[:300],
            )
        )

    return evidence


# =============================================================================
# CONFIDENCE
# =============================================================================

def _compute_confidence(
    chunks: List[RetrievedChunk],
) -> float:

    if not chunks:
        return 0.0

    scores = [
        chunk.score
        for chunk in chunks
        if chunk.score > 0
    ]

    if not scores:
        return 0.0

    confidence = (
        sum(scores)
        / len(scores)
    )

    return round(
        max(
            min(confidence, 1.0),
            0.0,
        ),
        4,
    )


# =============================================================================
# EMPTY DRAFT
# =============================================================================

def _empty_draft(
    doc_id: str,
    draft_type: DraftType,
) -> GeneratedDraft:

    return GeneratedDraft(
        doc_id=doc_id,
        draft_type=draft_type,
        content=(
            "No evidence could be "
            "retrieved from the document. "
            "Verify processing and indexing."
        ),
        evidence=[],
        generated_at=datetime.now(
            timezone.utc
        ),
        model_used=settings.MODEL_NAME,
        confidence_score=0.0,
    )