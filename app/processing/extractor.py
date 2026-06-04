import io
import logging
from datetime import datetime
from pathlib import Path

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageOps

from app.config import settings

logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

MIN_CHARS_PER_PAGE = 50

# Windows support
if hasattr(settings, "TESSERACT_CMD") and settings.TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD


# =============================================================================
# PUBLIC API
# =============================================================================

def extract_document(file_path: Path) -> dict:
    """
    Extract text from a PDF using:
    1. Direct PyMuPDF extraction
    2. OCR fallback for sparse pages

    Returns:
        {
            filename,
            page_count,
            ocr_pages,
            pages,
            raw_text,
            extracted_at
        }
    """

    logger.info(f"Starting extraction: {file_path.name}")

    _validate_file(file_path)

    pages = _extract_pages(file_path)

    raw_text = "\n\n".join(
        page["text"]
        for page in pages
        if page["text"].strip()
    )

    ocr_pages = sum(
        1 for page in pages
        if page["method"] == "ocr"
    )

    result = {
        "filename": file_path.name,
        "page_count": len(pages),
        "ocr_pages": ocr_pages,
        "pages": pages,
        "raw_text": raw_text,
        "extracted_at": datetime.utcnow().isoformat(),
    }

    logger.info(
        f"Extraction complete | "
        f"Pages={len(pages)} | "
        f"OCR Pages={ocr_pages} | "
        f"Characters={len(raw_text)}"
    )

    return result


# =============================================================================
# VALIDATION
# =============================================================================

def _validate_file(file_path: Path) -> None:

    if not file_path.exists():
        raise FileNotFoundError(
            f"Document not found: {file_path}"
        )

    if file_path.suffix.lower() != ".pdf":
        raise ValueError(
            f"Unsupported file type: {file_path.suffix}. "
            f"Only PDF files are supported."
        )


# =============================================================================
# PAGE EXTRACTION
# =============================================================================

def _extract_pages(file_path: Path) -> list[dict]:

    pages = []

    try:
        doc = fitz.open(str(file_path))
    except Exception as e:
        raise RuntimeError(
            f"Failed to open PDF: {e}"
        )

    try:
        for page_index in range(len(doc)):

            page = doc[page_index]

            text = _extract_text_pymupdf(page)

            if len(text.strip()) >= MIN_CHARS_PER_PAGE:

                pages.append({
                    "page_number": page_index + 1,
                    "text": text,
                    "method": "pymupdf",
                    "char_count": len(text),
                    "ocr_confidence": None,
                })

            else:

                logger.warning(
                    f"Page {page_index + 1}: "
                    f"Sparse text detected "
                    f"({len(text.strip())} chars). "
                    f"Switching to OCR."
                )

                ocr_text, confidence = _extract_text_ocr(page)

                pages.append({
                    "page_number": page_index + 1,
                    "text": ocr_text,
                    "method": "ocr",
                    "char_count": len(ocr_text),
                    "ocr_confidence": confidence,
                })

    finally:
        doc.close()

    return pages


# =============================================================================
# PYMUPDF EXTRACTION
# =============================================================================

def _extract_text_pymupdf(page) -> str:

    try:
        text = page.get_text("text")
        return text or ""

    except Exception as e:

        logger.error(
            f"PyMuPDF extraction failed: {e}"
        )

        return ""


# =============================================================================
# OCR EXTRACTION
# =============================================================================

def _extract_text_ocr(page) -> tuple[str, float]:

    try:

        # Render page at ~300 DPI
        matrix = fitz.Matrix(
            300 / 72,
            300 / 72
        )

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        image = Image.open(
            io.BytesIO(
                pix.tobytes("png")
            )
        )

        # OCR preprocessing
        image = image.convert("L")
        image = ImageOps.autocontrast(image)

        text = pytesseract.image_to_string(
            image,
            lang="eng",
            config="--psm 6"
        )

        confidence = _calculate_ocr_confidence(
            image
        )

        return text or "", confidence

    except Exception as e:

        logger.error(
            f"OCR extraction failed: {e}"
        )

        return (
            "[OCR FAILED - PAGE UNREADABLE]",
            0.0
        )


# =============================================================================
# OCR CONFIDENCE
# =============================================================================

def _calculate_ocr_confidence(
    image: Image.Image
) -> float:

    try:

        data = pytesseract.image_to_data(
            image,
            output_type=pytesseract.Output.DICT
        )

        confidences = []

        for conf in data["conf"]:

            try:
                value = float(conf)

                if value >= 0:
                    confidences.append(value)

            except Exception:
                continue

        if not confidences:
            return 0.0

        return round(
            sum(confidences) / len(confidences),
            2
        )

    except Exception:

        return 0.0


# =============================================================================
# SCANNED PDF DETECTION
# =============================================================================

def is_scanned_pdf(
    file_path: Path
) -> bool:

    try:

        doc = fitz.open(str(file_path))

        sparse_pages = 0
        total_pages = len(doc)

        for page in doc:

            text = page.get_text("text")

            if len(text.strip()) < MIN_CHARS_PER_PAGE:
                sparse_pages += 1

        doc.close()

        ratio = sparse_pages / max(
            total_pages,
            1
        )

        return ratio > 0.5

    except Exception:

        return False