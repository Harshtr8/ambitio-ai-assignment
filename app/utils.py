import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.config import settings
from app.models import ProcessedDocument

logger = logging.getLogger(__name__)


# =============================================================================
# LOGGING
# =============================================================================

def setup_logging(level: str = "INFO") -> None:
    """
    Configure application-wide logging.
    Call once during FastAPI startup.
    """

    logging.basicConfig(
        level=getattr(
            logging,
            level.upper(),
            logging.INFO,
        ),
        format=(
            "%(asctime)s | "
            "%(levelname)-8s | "
            "%(name)s | "
            "%(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )


# =============================================================================
# FILE HELPERS
# =============================================================================

def file_exists(path: Path) -> bool:
    """
    Safe file existence check.
    """

    return (
        path.exists()
        and path.is_file()
    )


# =============================================================================
# JSON STORAGE
# =============================================================================

def save_json(
    data: Union[Dict, List],
    path: Path,
) -> None:
    """
    Save JSON atomically.

    Prevents partially-written files
    if the application crashes.
    """

    try:

        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temp_path = path.with_suffix(
            path.suffix + ".tmp"
        )

        with open(
            temp_path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        temp_path.replace(path)

        logger.debug(
            f"Saved JSON: {path}"
        )

    except Exception as e:

        logger.error(
            f"Failed to save JSON "
            f"to {path}: {e}"
        )

        raise


def load_json(
    path: Path,
    default: Optional[
        Union[Dict, List]
    ] = None,
) -> Union[Dict, List]:
    """
    Load JSON safely.

    Returns default value if:
    - file doesn't exist
    - file is empty
    - JSON is invalid
    """

    if not file_exists(path):

        return (
            default
            if default is not None
            else {}
        )

    try:

        with open(
            path,
            "r",
            encoding="utf-8",
        ) as f:

            content = (
                f.read().strip()
            )

            if not content:

                return (
                    default
                    if default is not None
                    else {}
                )

            return json.loads(content)

    except json.JSONDecodeError:

        logger.warning(
            f"Invalid JSON found: {path}"
        )

        return (
            default
            if default is not None
            else {}
        )

    except Exception as e:

        logger.error(
            f"Failed loading JSON "
            f"from {path}: {e}"
        )

        raise


# =============================================================================
# PROCESSED DOCUMENT STORAGE
# =============================================================================

def save_processed_document(
    document: ProcessedDocument,
) -> Path:
    """
    Save ProcessedDocument to:

    data/processed/<doc_id>.json
    """

    output_path = (
        settings.PROCESSED_DIR
        / f"{document.doc_id}.json"
    )

    save_json(
        document.model_dump(
            mode="json"
        ),
        output_path,
    )

    logger.info(
        f"Saved processed document: "
        f"{output_path}"
    )

    return output_path


def load_processed_document(
    doc_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Load processed document.
    """

    path = (
        settings.PROCESSED_DIR
        / f"{doc_id}.json"
    )

    if not file_exists(path):

        logger.warning(
            f"Processed document "
            f"not found: {doc_id}"
        )

        return None

    return load_json(path)


# =============================================================================
# EDIT STORE
# =============================================================================

def load_edit_store() -> List[Dict]:
    """
    Load all operator edits.
    """

    return load_json(
        settings.EDIT_STORE_PATH,
        default=[],
    )


def append_edit(
    edit: Dict[str, Any],
) -> None:
    """
    Append edit to edit_store.json
    """

    edits = load_edit_store()

    edits.append(edit)

    save_json(
        edits,
        settings.EDIT_STORE_PATH,
    )

    logger.info(
        f"Edit appended | "
        f"doc_id={edit.get('doc_id')}"
    )


# =============================================================================
# LEARNED PATTERN STORE
# =============================================================================

def load_learned_patterns() -> List[Dict]:
    """
    Load learned patterns.
    """

    return load_json(
        settings.LEARNED_PATTERNS_PATH,
        default=[],
    )


def save_learned_patterns(
    patterns: List[Dict],
) -> None:
    """
    Save learned patterns.
    """

    save_json(
        patterns,
        settings.LEARNED_PATTERNS_PATH,
    )

    logger.info(
        f"Saved "
        f"{len(patterns)} "
        f"learned patterns"
    )


# =============================================================================
# ID GENERATION
# =============================================================================

def generate_pattern_id() -> str:
    """
    Example:
    pat_a3f9b12c
    """

    return (
        f"pat_{uuid.uuid4().hex[:8]}"
    )


# =============================================================================
# DATETIME HELPERS
# =============================================================================

def utcnow() -> datetime:
    """
    Timezone-aware UTC datetime.
    """

    return datetime.now(
        timezone.utc
    )


def utcnow_isoformat() -> str:
    """
    ISO-8601 UTC timestamp.
    """

    return utcnow().isoformat()