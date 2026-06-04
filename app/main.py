from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.models import (
    DraftRequest,
    DraftResponse,
    FeedbackRequest,
    FeedbackResponse,
    ProcessRequest,
    ProcessResponse,
)
from app.processing import process_document
from app.retriever import (
    get_index_stats,
    index_document,
)
from app.drafter import generate_draft
from app.feedback import (
    process_feedback,
    get_learning_stats,
)
from app.utils import (
    save_processed_document,
    setup_logging,
)

# =============================================================================
# STARTUP
# =============================================================================

setup_logging()

app = FastAPI(
    title="Ambitio Document Intelligence Pipeline",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HEALTH
# =============================================================================

@app.get("/")
def root():

    return {
        "message":
            "Ambitio Document Intelligence Pipeline",
        "status":
            "running",
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# =============================================================================
# DOCUMENT PROCESSING
# =============================================================================

@app.post(
    "/process",
    response_model=ProcessResponse,
)
def process_document_endpoint(
    request: ProcessRequest,
):

    try:

        file_path = (
            Path("data/sample_docs")
            / request.filename
        )

        document = process_document(
            file_path
        )

        index_document(
            document.chunks
        )

        save_processed_document(
            document
        )

        return ProcessResponse(
            success=True,
            doc_id=document.doc_id,
            filename=document.filename,
            chunk_count=len(
                document.chunks
            ),
            page_count=document.metadata.page_count,
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e),
        )


# =============================================================================
# DRAFT GENERATION
# =============================================================================

@app.post(
    "/draft",
    response_model=DraftResponse,
)
def draft_endpoint(
    request: DraftRequest,
):

    try:

        draft = generate_draft(
            doc_id=request.doc_id,
            draft_type=request.draft_type,
        )

        return DraftResponse(
            success=True,
            doc_id=request.doc_id,
            draft=draft,
        )

    except Exception as e:

        return DraftResponse(
            success=False,
            doc_id=request.doc_id,
            error=str(e),
        )


# =============================================================================
# FEEDBACK
# =============================================================================

@app.post(
    "/feedback",
    response_model=FeedbackResponse,
)
def feedback_endpoint(
    request: FeedbackRequest,
):

    try:

        patterns = process_feedback(
            request
        )

        return FeedbackResponse(
            success=True,
            patterns_extracted=len(
                patterns
            ),
            message=(
                "Feedback processed "
                "successfully."
            ),
        )

    except Exception as e:

        return FeedbackResponse(
            success=False,
            patterns_extracted=0,
            message=str(e),
        )


# =============================================================================
# DEBUG / METRICS
# =============================================================================

@app.get("/stats/index")
def index_stats():

    return get_index_stats()


@app.get("/stats/learning")
def learning_stats():

    return get_learning_stats()