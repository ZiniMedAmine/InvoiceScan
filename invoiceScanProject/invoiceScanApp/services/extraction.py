"""
Document classification and data structuring with Google Gemini.

The raw OCR text is sent to Gemini together with the prompt stored in
``prompts/extraction_prompt.txt``. The model answers with a line such as
``*Document Type: Invoice*`` followed by a JSON object describing the data.
"""

import json
import logging
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from django.conf import settings
from google import genai
from google.genai import errors as genai_errors

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "extraction_prompt.txt"
DOCUMENT_TYPE_PATTERN = re.compile(r"document\s*type\s*:?\s*(.+)", re.IGNORECASE)
UNKNOWN_DOCUMENT_TYPE = "Unknown"


class ExtractionError(Exception):
    """Raised when Gemini cannot be reached or returns no usable answer."""


@dataclass(frozen=True)
class ExtractionResult:
    document_type: str
    # Pretty-printed JSON, or the raw answer if the model produced invalid
    # JSON (the user can then fix it on the review page).
    json_text: str


@cache
def load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


@cache
def get_client() -> genai.Client:
    if not settings.GEMINI_API_KEY:
        raise ExtractionError("GEMINI_API_KEY is not configured.")
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def structure_text(ocr_text: str) -> ExtractionResult:
    """Ask Gemini to classify the document and organise its text as JSON."""
    prompt = f"{load_prompt()}\n{ocr_text}"
    try:
        response = get_client().models.generate_content(
            model=settings.GEMINI_MODEL, contents=prompt,
        )
    except genai_errors.APIError as exc:
        logger.exception("Gemini request failed")
        raise ExtractionError(f"The AI service returned an error: {exc}") from exc

    if not response.text:
        raise ExtractionError("The AI service returned an empty answer.")
    return parse_model_response(response.text)


def parse_model_response(text: str) -> ExtractionResult:
    """
    Split a Gemini answer into the document type and the JSON payload.

    The JSON is located between the first ``{`` and the last ``}``, which makes
    the parsing robust to Markdown code fences or extra sentences around it.
    """
    start, end = text.find("{"), text.rfind("}")
    has_json = start != -1 and end > start

    header = text[:start] if has_json else text
    match = DOCUMENT_TYPE_PATTERN.search(header)
    document_type = match.group(1).strip(" *_`#\t") if match else ""

    json_text = text[start:end + 1] if has_json else text.strip()
    try:
        json_text = json.dumps(json.loads(json_text), indent=2, ensure_ascii=False)
    except json.JSONDecodeError:
        logger.warning("Gemini returned invalid JSON, the user will have to fix it.")

    return ExtractionResult(document_type or UNKNOWN_DOCUMENT_TYPE, json_text)
