"""Orchestration of the whole scan: preprocessing -> OCR -> AI structuring."""

import logging
import time
from contextlib import contextmanager

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import UploadedFile

from ..models import ScannedDocument
from .extraction import ExtractionError, structure_text
from .ocr import extract_text
from .preprocessing import encode_png, load_image, preprocess_image

logger = logging.getLogger(__name__)


@contextmanager
def timed(step: str):
    """Log how long a step of the pipeline takes."""
    start = time.perf_counter()
    yield
    logger.info("%s took %.2f s", step, time.perf_counter() - start)


def scan_document(uploaded_file: UploadedFile) -> ScannedDocument:
    """
    Store an uploaded image and extract its structured data.

    Raises ``ExtractionError`` if the image cannot be decoded or the AI
    service fails.
    """
    document = ScannedDocument.objects.create(image=uploaded_file)

    with document.image.open("rb") as image_file:
        try:
            image = load_image(image_file.read())
        except ValueError as exc:
            raise ExtractionError(f"{document.filename} could not be read as an image.") from exc

    with timed("Preprocessing"):
        preprocessed = preprocess_image(image)
    document.preprocessed_image.save(
        f"{document.stem}_preprocessed.png", ContentFile(encode_png(preprocessed)), save=False,
    )

    with timed("OCR"):
        ocr_text = extract_text(preprocessed)

    with timed("AI structuring"):
        result = structure_text(ocr_text)

    document.document_type = result.document_type
    document.extracted_text = result.json_text
    document.save()
    return document
