import json
import logging
from datetime import datetime, timezone
from typing import List

import google.generativeai as genai

from app.config import settings
from app.models import (
    FeedbackRequest,
    LearnedPattern,
    PatternType,
)
from app.prompts import (
    FEEDBACK_SYSTEM_PROMPT,
    PATTERN_EXTRACTION_PROMPT,
)
from app.utils import (
    append_edit,
    generate_pattern_id,
    load_learned_patterns,
    save_learned_patterns,
)

logger = logging.getLogger(__name__)


# =============================================================================
# GEMINI CONFIGURATION
# =============================================================================

genai.configure(
    api_key=settings.GEMINI_API_KEY
)


def _get_model():

    return genai.GenerativeModel(
        model_name=settings.MODEL_NAME,
        system_instruction=FEEDBACK_SYSTEM_PROMPT,
    )


# =============================================================================
# PUBLIC API
# =============================================================================

def process_feedback(
    feedback: FeedbackRequest,
) -> List[LearnedPattern]:
    """
    Process operator edits and learn reusable patterns.

    Flow:

    Save Edit
      ↓
    Gemini Pattern Extraction
      ↓
    Deduplicate
      ↓
    Frequency Update
      ↓
    Persist Patterns
    """

    logger.info(
        f"Processing feedback | "
        f"doc_id={feedback.doc_id}"
    )

    # -------------------------------------------------
    # Save raw edit
    # -------------------------------------------------

    append_edit(
        {
            "doc_id": feedback.doc_id,
            "draft_type": feedback.draft_type,
            "original_draft": feedback.original_draft,
            "edited_draft": feedback.edited_draft,
            "edited_at": datetime.now(
                timezone.utc
            ).isoformat(),
        }
    )

    # -------------------------------------------------
    # Extract reusable patterns
    # -------------------------------------------------

    extracted_patterns = (
        _extract_patterns(
            feedback.original_draft,
            feedback.edited_draft,
        )
    )

    if not extracted_patterns:

        logger.info(
            "No reusable patterns found."
        )

        return []

    # -------------------------------------------------
    # Merge with existing patterns
    # -------------------------------------------------

    existing_patterns = (
        load_learned_patterns()
    )

    updated_patterns = (
        _merge_patterns(
            existing_patterns,
            extracted_patterns,
        )
    )

    save_learned_patterns(
        updated_patterns
    )

    logger.info(
        f"Patterns learned: "
        f"{len(extracted_patterns)}"
    )

    return [
    LearnedPattern(
        pattern_id=p.get(
            "pattern_id",
            generate_pattern_id(),
        ),
        pattern_type=p.get(
            "pattern_type",
            PatternType.TERMINOLOGY.value,
        ),
        description=p.get(
            "description",
            "",
        ),
        original_phrasing=p.get(
            "original_phrasing",
            "",
        ),
        preferred_phrasing=p.get(
            "preferred_phrasing",
            "",
        ),
        frequency=p.get(
            "frequency",
            1,
        ),
        last_seen=datetime.now(
            timezone.utc
        ),
    )
    for p in extracted_patterns
]


# =============================================================================
# GEMINI EXTRACTION
# =============================================================================

def _extract_patterns(
    original_draft: str,
    edited_draft: str,
) -> List[dict]:

    prompt = (
        PATTERN_EXTRACTION_PROMPT
        .format(
            original_draft=original_draft,
            edited_draft=edited_draft,
        )
    )

    try:

        model = _get_model()

        response = (
            model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.0,
                    max_output_tokens=2048,
                ),
            )
        )

        text = (
            response.text
            .strip()
        )

        if text.startswith("```"):

            text = (
                text.replace(
                    "```json",
                    "",
                )
                .replace(
                    "```",
                    "",
                )
                .strip()
            )

        patterns = json.loads(
            text
        )

        if not isinstance(
            patterns,
            list,
        ):
            return []

        return patterns

    except Exception as e:

        logger.error(
            f"Pattern extraction failed: "
            f"{e}"
        )

        return []


# =============================================================================
# MERGING
# =============================================================================

def _merge_patterns(
    existing_patterns: List[dict],
    new_patterns: List[dict],
) -> List[dict]:
    """
    Deduplicate and update frequencies.
    """

    now = datetime.now(
        timezone.utc
    ).isoformat()

    existing_lookup = {}

    for pattern in existing_patterns:

        key = (
            pattern.get(
                "original_phrasing",
                "",
            ).strip().lower(),
            pattern.get(
                "preferred_phrasing",
                "",
            ).strip().lower(),
        )

        existing_lookup[key] = (
            pattern
        )

    for pattern in new_patterns:

        key = (
            pattern.get(
                "original_phrasing",
                "",
            ).strip().lower(),
            pattern.get(
                "preferred_phrasing",
                "",
            ).strip().lower(),
        )

        if key in existing_lookup:

            existing_lookup[key][
                "frequency"
            ] += 1

            existing_lookup[key][
                "last_seen"
            ] = now

        else:

            existing_lookup[key] = {
                "pattern_id":
                    generate_pattern_id(),

                "pattern_type":
                    pattern.get(
                        "pattern_type",
                        PatternType.TERMINOLOGY.value,
                    ),

                "description":
                    pattern.get(
                        "description",
                        "",
                    ),

                "original_phrasing":
                    pattern.get(
                        "original_phrasing",
                        "",
                    ),

                "preferred_phrasing":
                    pattern.get(
                        "preferred_phrasing",
                        "",
                    ),

                "frequency": 1,

                "last_seen": now,
            }

    return list(
        existing_lookup.values()
    )


# =============================================================================
# STATS
# =============================================================================

def get_learning_stats() -> dict:
    """
    Return learning metrics.
    """

    patterns = (
        load_learned_patterns()
    )

    if not patterns:

        return {
            "total_patterns": 0,
            "most_common_pattern": None,
        }

    sorted_patterns = sorted(
        patterns,
        key=lambda p: p.get(
            "frequency",
            0,
        ),
        reverse=True,
    )

    return {
        "total_patterns":
            len(patterns),

        "most_common_pattern":
            sorted_patterns[0].get(
                "description"
            ),

        "max_frequency":
            sorted_patterns[0].get(
                "frequency"
            ),
    }