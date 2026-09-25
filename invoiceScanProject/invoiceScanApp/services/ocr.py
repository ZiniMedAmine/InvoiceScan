"""Text recognition with Tesseract OCR."""

import logging
import re

import numpy as np
import pytesseract
from django.conf import settings

logger = logging.getLogger(__name__)

# --psm 12: sparse text with orientation and script detection (invoices are
#           made of scattered blocks rather than paragraphs).
# --oem 1:  LSTM neural network engine only.
TESSERACT_CONFIG = "--psm 12 --oem 1"

# Characters kept after OCR: letters, digits, whitespace and a few symbols that
# carry meaning in invoices (dates, amounts, e-mails, percentages, ...).
UNWANTED_CHARS = re.compile(r"[^\w\s\-&./%@+]")
WHITESPACE = re.compile(r"\s+")


def extract_text(image: np.ndarray) -> str:
    """Run Tesseract on a preprocessed image and return the cleaned text."""
    if settings.TESSERACT_CMD:
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

    raw_text = pytesseract.image_to_string(
        image, lang=settings.TESSERACT_LANG, config=TESSERACT_CONFIG,
    )
    text = clean_text(raw_text)
    logger.debug("OCR output: %s", text)
    return text


def clean_text(text: str) -> str:
    """Collapse whitespace and strip noise characters produced by the OCR."""
    text = WHITESPACE.sub(" ", text).strip()
    return UNWANTED_CHARS.sub("", text)
