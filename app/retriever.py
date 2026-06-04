import logging
import pickle
from typing import List, Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings
from app.models import (
    Chunk,
    RetrievedChunk,
    RetrievalResult,
)
from app.utils import utcnow

logger = logging.getLogger(__name__)


# =============================================================================
# STORAGE PATHS
# =============================================================================

FAISS_INDEX_PATH = (
    settings.FAISS_INDEX_DIR
    / "index.faiss"
)

CHUNKS_STORE_PATH = (
    settings.FAISS_INDEX_DIR
    / "chunks.pkl"
)


# =============================================================================
# EMBEDDING MODEL
# =============================================================================

_embedding_model: Optional[
    SentenceTransformer
] = None


def _get_embedding_model() -> SentenceTransformer:
    """
    Lazy-load embedding model.
    """

    global _embedding_model

    if _embedding_model is None:

        logger.info(
            f"Loading embedding model: "
            f"{settings.EMBEDDING_MODEL}"
        )

        _embedding_model = (
            SentenceTransformer(
                settings.EMBEDDING_MODEL
            )
        )

        logger.info(
            "Embedding model loaded."
        )

    return _embedding_model


# =============================================================================
# PUBLIC API
# =============================================================================

def index_document(
    chunks: List[Chunk],
) -> None:
    """
    Index document chunks into FAISS.

    Duplicate chunk IDs are ignored.
    """

    if not chunks:

        logger.warning(
            "No chunks provided for indexing."
        )

        return

    index, stored_chunks = _load_index()

    existing_chunk_ids = {
        chunk.chunk_id
        for chunk in stored_chunks
    }

    new_chunks = [
        chunk
        for chunk in chunks
        if chunk.chunk_id
        not in existing_chunk_ids
    ]

    if not new_chunks:

        logger.info(
            "All chunks already indexed."
        )

        return

    logger.info(
        f"Indexing "
        f"{len(new_chunks)} chunks..."
    )

    model = _get_embedding_model()

    texts = [
        chunk.text
        for chunk in new_chunks
    ]

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=False,
    )

    embeddings = np.asarray(
        embeddings,
        dtype=np.float32,
    )

    if index is None:

        dimension = embeddings.shape[1]

        index = faiss.IndexFlatIP(
            dimension
        )

        logger.info(
            f"Created new FAISS index "
            f"(dim={dimension})"
        )

    index.add(embeddings)

    stored_chunks.extend(
        new_chunks
    )

    _save_index(
        index=index,
        chunks=stored_chunks,
    )

    logger.info(
        f"Indexing complete | "
        f"total_chunks={index.ntotal}"
    )


def retrieve(
    query: str,
    doc_id: Optional[str] = None,
    top_k: Optional[int] = None,
) -> RetrievalResult:
    """
    Retrieve relevant chunks.
    """

    start_time = utcnow()

    top_k = (
        top_k
        or settings.TOP_K_CHUNKS
    )

    index, stored_chunks = (
        _load_index()
    )

    if (
        index is None
        or index.ntotal == 0
    ):

        logger.warning(
            "FAISS index is empty."
        )

        return RetrievalResult(
            query=query,
            retrieved_chunks=[],
            total_retrieved=0,
            retrieval_time_ms=0.0,
        )

    model = _get_embedding_model()

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True,
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype=np.float32,
    )

    if doc_id:

        search_k = min(
            max(top_k * 10, 50),
            index.ntotal,
        )

    else:

        search_k = min(
            top_k,
            index.ntotal,
        )

    scores, indices = index.search(
        query_embedding,
        search_k,
    )

    retrieved = []

    for score, idx in zip(
        scores[0],
        indices[0],
    ):

        if (
            idx < 0
            or idx >= len(stored_chunks)
        ):
            continue

        chunk = stored_chunks[idx]

        if (
            doc_id
            and chunk.doc_id != doc_id
        ):
            continue

        retrieved.append(
            RetrievedChunk(
                chunk_id=chunk.chunk_id,
                doc_id=chunk.doc_id,
                text=chunk.text,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                score=round(
                    float(score),
                    4,
                ),
            )
        )

        if len(retrieved) >= top_k:
            break

    elapsed_ms = (
        utcnow() - start_time
    ).total_seconds() * 1000

    logger.info(
        f"Retrieval complete | "
        f"retrieved={len(retrieved)} | "
        f"time={elapsed_ms:.2f}ms"
    )

    return RetrievalResult(
        query=query,
        retrieved_chunks=retrieved,
        total_retrieved=len(
            retrieved
        ),
        retrieval_time_ms=round(
            elapsed_ms,
            2,
        ),
    )


# =============================================================================
# INDEX STORAGE
# =============================================================================

def _load_index():
    """
    Load FAISS index and chunk store.
    """

    if (
        not FAISS_INDEX_PATH.exists()
        or not CHUNKS_STORE_PATH.exists()
    ):
        return None, []

    try:

        index = faiss.read_index(
            str(
                FAISS_INDEX_PATH
            )
        )

        with open(
            CHUNKS_STORE_PATH,
            "rb",
        ) as f:

            stored_chunks = (
                pickle.load(f)
            )

        return (
            index,
            stored_chunks,
        )

    except Exception as e:

        logger.error(
            f"Failed to load "
            f"FAISS index: {e}"
        )

        return None, []


def _save_index(
    index,
    chunks: List[Chunk],
) -> None:
    """
    Save FAISS index and chunk store.
    """

    try:

        settings.FAISS_INDEX_DIR.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            index,
            str(
                FAISS_INDEX_PATH
            ),
        )

        with open(
            CHUNKS_STORE_PATH,
            "wb",
        ) as f:

            pickle.dump(
                chunks,
                f,
            )

    except Exception as e:

        logger.error(
            f"Failed to save "
            f"FAISS index: {e}"
        )

        raise


# =============================================================================
# MAINTENANCE
# =============================================================================

def clear_index() -> None:
    """
    Remove all indexed data.
    """

    for path in [
        FAISS_INDEX_PATH,
        CHUNKS_STORE_PATH,
    ]:

        if path.exists():

            path.unlink()

            logger.info(
                f"Deleted: {path}"
            )

    logger.info(
        "FAISS index cleared."
    )


def get_index_stats() -> dict:
    """
    Return index statistics.
    """

    index, stored_chunks = (
        _load_index()
    )

    if index is None:

        return {
            "status": "empty",
            "total_chunks": 0,
            "unique_documents": 0,
        }

    unique_documents = len(
        {
            chunk.doc_id
            for chunk in stored_chunks
        }
    )

    return {
        "status": "ready",
        "total_chunks": index.ntotal,
        "unique_documents": unique_documents,
        "embedding_model": settings.EMBEDDING_MODEL,
        "index_path": str(
            FAISS_INDEX_PATH
        ),
    }