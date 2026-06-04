import hashlib
import logging
import re
from typing import List

from app.config import settings
from app.models import Chunk

logger = logging.getLogger(__name__)


# =============================================================================
# PUBLIC API
# =============================================================================

def chunk_document(cleaned: dict) -> List[Chunk]:
    """
    Convert cleaned document into retrieval-ready chunks.

    Strategy:
    1. Process page-by-page
    2. Split into sentences
    3. Build semantic chunks
    4. Apply sentence overlap
    5. Generate Chunk objects
    """

    logger.info(
        f"Chunking document: {cleaned['filename']}"
    )

    doc_id = _generate_doc_id(
        cleaned["filename"]
    )

    chunks = []
    chunk_index = 0

    for page in cleaned["pages"]:

        page_text = page["text"].strip()
        page_number = page["page_number"]

        if not page_text:
            continue

        if page_text.startswith("[OCR FAILED"):
            logger.warning(
                f"Skipping unreadable page {page_number}"
            )
            continue

        page_chunks = _split_into_chunks(
            text=page_text,
            chunk_size=settings.CHUNK_SIZE,
            overlap_sentences=2,
        )

        for chunk_text in page_chunks:

            chunk_text = chunk_text.strip()

            if not chunk_text:
                continue

            chunk_id = _generate_chunk_id(
                doc_id=doc_id,
                page_number=page_number,
                chunk_index=chunk_index,
            )

            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    doc_id=doc_id,
                    text=chunk_text,
                    page_number=page_number,
                    chunk_index=chunk_index,
                    char_count=len(chunk_text),
                )
            )

            chunk_index += 1

    logger.info(
        f"Chunking complete | "
        f"Chunks={len(chunks)} | "
        f"Document={cleaned['filename']}"
    )

    return chunks


# =============================================================================
# CHUNKING
# =============================================================================

def _split_into_chunks(
    text: str,
    chunk_size: int,
    overlap_sentences: int = 2,
) -> List[str]:
    """
    Create semantic chunks using sentence boundaries.

    Uses sentence overlap instead of character overlap
    to preserve context for retrieval.
    """

    sentences = _split_into_sentences(text)

    if not sentences:
        return []

    chunks = []

    current_sentences = []
    current_length = 0

    for sentence in sentences:

        # Handle extremely long sentences
        if len(sentence) > chunk_size:

            long_parts = _split_long_sentence(
                sentence,
                chunk_size,
            )

            for part in long_parts:

                if current_sentences:
                    chunks.append(
                        " ".join(current_sentences)
                    )

                    current_sentences = []
                    current_length = 0

                chunks.append(part)

            continue

        proposed_length = (
            current_length
            + len(sentence)
        )

        if (
            proposed_length > chunk_size
            and current_sentences
        ):

            chunks.append(
                " ".join(current_sentences)
            )

            overlap = current_sentences[
                -overlap_sentences:
            ]

            current_sentences = (
                overlap + [sentence]
            )

            current_length = sum(
                len(s)
                for s in current_sentences
            )

        else:

            current_sentences.append(
                sentence
            )

            current_length += len(sentence)

    if current_sentences:

        chunks.append(
            " ".join(current_sentences)
        )

    return chunks


def _split_long_sentence(
    sentence: str,
    max_size: int,
) -> List[str]:
    """
    Fallback splitter for unusually long legal sentences.
    """

    if len(sentence) <= max_size:
        return [sentence]

    return [
        sentence[i:i + max_size]
        for i in range(
            0,
            len(sentence),
            max_size,
        )
    ]


# =============================================================================
# SENTENCE SPLITTING
# =============================================================================

def _split_into_sentences(
    text: str,
) -> List[str]:
    """
    Legal-document-friendly sentence splitter.
    """

    abbreviations = [
        "vs.",
        "v.",
        "no.",
        "sec.",
        "art.",
        "para.",
        "ref.",
        "dept.",
        "corp.",
        "inc.",
        "ltd.",
        "co.",
        "mr.",
        "mrs.",
        "dr.",
        "prof.",
        "govt.",
        "approx.",
        "vol.",
        "p.",
        "pp.",
        "fig.",
        "est.",
    ]

    protected = text
    placeholders = {}

    for i, abbr in enumerate(
        abbreviations
    ):

        placeholder = (
            f"__ABBR{i}__"
        )

        placeholders[
            placeholder
        ] = abbr

        protected = re.sub(
            re.escape(abbr),
            placeholder,
            protected,
            flags=re.IGNORECASE,
        )

    raw_sentences = re.split(
        r"(?<=[.!?])\s+(?=[A-Z])",
        protected,
    )

    sentences = []

    for sentence in raw_sentences:

        parts = sentence.split("\n")

        for part in parts:

            cleaned = part.strip()

            if cleaned:
                sentences.append(
                    cleaned
                )

    restored = []

    for sentence in sentences:

        for placeholder, abbr in (
            placeholders.items()
        ):

            sentence = sentence.replace(
                placeholder,
                abbr,
            )

        sentence = sentence.strip()

        if sentence:
            restored.append(
                sentence
            )

    return restored


# =============================================================================
# ID GENERATION
# =============================================================================

def _generate_doc_id(
    filename: str,
) -> str:
    """
    Generate stable document ID.

    Example:
    contract.pdf
    -> doc_a3f9b12c
    """

    hash_value = hashlib.md5(
        filename.encode("utf-8")
    ).hexdigest()[:8]

    return f"doc_{hash_value}"


def _generate_chunk_id(
    doc_id: str,
    page_number: int,
    chunk_index: int,
) -> str:
    """
    Example:
    doc_a3f9b12c_p02_c005
    """

    return (
        f"{doc_id}"
        f"_p{page_number:02d}"
        f"_c{chunk_index:03d}"
    )