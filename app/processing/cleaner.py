import logging
import re
import unicodedata

logger = logging.getLogger(__name__)


# =============================================================================
# PUBLIC API
# =============================================================================

def clean_document(extracted: dict) -> dict:
    """
    Clean extracted document pages.

    Input:
        Output dict from extract_document()

    Output:
        Same structure with cleaned text fields.
    """

    logger.info(
        f"Cleaning document: {extracted['filename']}"
    )

    cleaned_pages = []

    for page in extracted["pages"]:

        raw_text = page["text"]

        cleaned_text = _clean_page(
            raw_text
        )

        cleaned_pages.append({
            **page,
            "text": cleaned_text,
            "original_text": raw_text,
            "char_count": len(cleaned_text),
            "cleaning_stats": get_cleaning_stats(
                raw_text,
                cleaned_text
            )
        })

    cleaned_raw_text = "\n\n".join(
        page["text"]
        for page in cleaned_pages
        if page["text"].strip()
    )

    return {
        **extracted,
        "pages": cleaned_pages,
        "raw_text": cleaned_raw_text,
        "cleaning_report": document_cleaning_report(
            cleaned_pages
        )
    }


# =============================================================================
# PAGE CLEANING
# =============================================================================

def _clean_page(text: str) -> str:
    """
    Apply all cleaning operations to a page.
    """

    if not text or not text.strip():
        return ""

    # Preserve extractor failure markers
    if text.startswith("[OCR FAILED"):
        return text

    text = _normalize_unicode(text)

    text = _remove_control_characters(text)

    text = _fix_ocr_errors(text)

    text = _repair_hyphenated_words(text)

    text = _normalize_whitespace(text)

    text = _remove_page_artifacts(text)

    return text.strip()


# =============================================================================
# CLEANING STEPS
# =============================================================================

def _normalize_unicode(text: str) -> str:
    """
    Normalize Unicode into NFC form.
    """

    try:
        return unicodedata.normalize(
            "NFC",
            text
        )
    except Exception:
        return text


def _remove_control_characters(
    text: str
) -> str:
    """
    Remove non-printable control chars.
    Preserve newlines and tabs.
    """

    cleaned = []

    for char in text:

        category = unicodedata.category(
            char
        )

        if (
            category == "Cc"
            and char not in ("\n", "\t")
        ):
            continue

        cleaned.append(char)

    return "".join(cleaned)


def _fix_ocr_errors(text: str) -> str:
    """
    Fix common OCR artifacts.

    Keep this conservative.
    Over-aggressive OCR correction can
    damage valid legal text.
    """

    replacements = [

        # Ligatures
        ("ﬁ", "fi"),
        ("ﬂ", "fl"),
        ("ﬀ", "ff"),
        ("ﬃ", "ffi"),
        ("ﬄ", "ffl"),

        # Smart quotes
        ("\u2018", "'"),
        ("\u2019", "'"),
        ("\u201c", '"'),
        ("\u201d", '"'),

        # Dashes
        ("\u2014", " - "),
        ("\u2013", " - "),
    ]

    for old, new in replacements:
        text = text.replace(old, new)

    # Example:
    # operati0n -> operation
    text = re.sub(
        r"(?<=[a-z])0(?=[a-z])",
        "o",
        text
    )

    # Example:
    # va1ue -> value
    text = re.sub(
        r"(?<=[a-z])1(?=[a-z])",
        "l",
        text
    )

    return text


def _repair_hyphenated_words(
    text: str
) -> str:
    """
    Join PDF line-break hyphenations.

    Example:
        docu-
        ment

    becomes:
        document
    """

    return re.sub(
        r"(\w)-\n(\w)",
        r"\1\2",
        text
    )


def _normalize_whitespace(
    text: str
) -> str:
    """
    Normalize whitespace while preserving
    paragraph structure.
    """

    text = text.replace("\t", " ")

    text = re.sub(
        r" {2,}",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    text = re.sub(
        r" +\n",
        "\n",
        text
    )

    text = re.sub(
        r"\n +",
        "\n",
        text
    )

    return text


def _remove_page_artifacts(
    text: str
) -> str:
    """
    Remove common PDF artifacts.
    """

    # Page 4
    text = re.sub(
        r"(?i)\bpage\s+\d+\b",
        "",
        text
    )

    # - 4 -
    text = re.sub(
        r"-\s*\d+\s*-",
        "",
        text
    )

    # Standalone page number
    text = re.sub(
        r"^\s*\d+\s*$",
        "",
        text,
        flags=re.MULTILINE
    )

    # Form feed
    text = text.replace(
        "\f",
        "\n"
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text


# =============================================================================
# REPORTING
# =============================================================================

def get_cleaning_stats(
    original: str,
    cleaned: str
) -> dict:

    return {
        "original_chars": len(original),
        "cleaned_chars": len(cleaned),
        "chars_removed": (
            len(original) - len(cleaned)
        ),
        "reduction_pct": round(
            (
                1
                - len(cleaned)
                / max(len(original), 1)
            )
            * 100,
            2
        )
    }


def document_cleaning_report(
    pages: list[dict]
) -> dict:
    """
    Aggregate document-level cleaning stats.
    """

    original_chars = sum(
        len(
            page.get(
                "original_text",
                ""
            )
        )
        for page in pages
    )

    cleaned_chars = sum(
        len(
            page.get(
                "text",
                ""
            )
        )
        for page in pages
    )

    return {
        "pages": len(pages),
        "original_chars": original_chars,
        "cleaned_chars": cleaned_chars,
        "chars_removed": (
            original_chars
            - cleaned_chars
        ),
        "reduction_pct": round(
            (
                1
                - cleaned_chars
                / max(original_chars, 1)
            )
            * 100,
            2
        )
    }