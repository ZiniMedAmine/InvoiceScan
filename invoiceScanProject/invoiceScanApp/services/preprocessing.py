"""
Image preprocessing that prepares a scanned document for OCR.

Pipeline::

    upscale x2 -> grayscale -> morphological noise removal
    -> adaptive threshold (block size derived from the text size) -> padding

The adaptive threshold needs a *block size* that matches the size of the
characters in the image, so the average character height is estimated first
from the contours of a quick Otsu binarisation.
"""

import logging
import math

import cv2
import numpy as np

logger = logging.getLogger(__name__)

UPSCALE_FACTOR = 2
NOISE_KERNEL = np.ones((2, 1), np.uint8)
DEFAULT_BLOCK_SIZE = 75
BORDER_SIZE = 5
# Stop searching for the threshold constant once the foreground/background
# ratio drops more than 5% below the best ratio seen so far.
RATIO_TOLERANCE = 0.95


def load_image(data: bytes) -> np.ndarray:
    """Decode an encoded image (JPEG, PNG, ...) into a BGR OpenCV array."""
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("The file could not be decoded as an image.")
    return image


def encode_png(image: np.ndarray) -> bytes:
    """Encode an OpenCV array as PNG bytes (lossless, ideal for binary images)."""
    success, buffer = cv2.imencode(".png", image)
    if not success:
        raise ValueError("The image could not be encoded as PNG.")
    return buffer.tobytes()


def preprocess_image(image: np.ndarray) -> np.ndarray:
    """Return a clean, binarised version of ``image`` ready for Tesseract."""
    height, width = image.shape[:2]
    upscaled = cv2.resize(image, (width * UPSCALE_FACTOR, height * UPSCALE_FACTOR))
    gray = cv2.cvtColor(upscaled, cv2.COLOR_BGR2GRAY)
    denoised = remove_noise(gray)

    block_size = compute_block_size(denoised, reference_height=height)
    logger.debug("Adaptive threshold block size: %d", block_size)

    binary = adaptive_threshold(denoised, block_size)
    return cv2.copyMakeBorder(
        binary, BORDER_SIZE, BORDER_SIZE, BORDER_SIZE, BORDER_SIZE,
        cv2.BORDER_CONSTANT, value=255,
    )


def remove_noise(image: np.ndarray) -> np.ndarray:
    """Remove small specks with a dilation, an erosion and a closing."""
    image = cv2.dilate(image, NOISE_KERNEL, iterations=1)
    image = cv2.erode(image, NOISE_KERNEL, iterations=1)
    return cv2.morphologyEx(image, cv2.MORPH_CLOSE, NOISE_KERNEL)


def estimate_char_height(gray: np.ndarray) -> float | None:
    """
    Estimate the average height (in pixels) of the characters in ``gray``.

    The image is binarised with Otsu's method and every external contour whose
    bounding box looks like a character (plausible size and aspect ratio) is
    kept. Returns ``None`` when no character-like contour is found.
    """
    _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    heights = []
    for contour in contours:
        _, _, w, h = cv2.boundingRect(contour)
        if 0.2 < w / h < 1.5 and 5 < w < 20 and 5 < h < 30:
            heights.append(h)

    return sum(heights) / len(heights) if heights else None


def compute_block_size(gray: np.ndarray, reference_height: int) -> int:
    """
    Pick the adaptive-threshold block size for ``gray``.

    It is the number of text lines that would fit in ``reference_height``
    (image height / average character height), rounded to an odd number as
    required by OpenCV.
    """
    char_height = estimate_char_height(gray)
    if char_height is None:
        logger.info("No text detected, using the default block size (%d).", DEFAULT_BLOCK_SIZE)
        return DEFAULT_BLOCK_SIZE
    return max(3, round_to_odd(reference_height / char_height))


def round_to_odd(value: float) -> int:
    """Round ``value`` to the nearest odd integer."""
    return 2 * math.floor(value / 2) + 1


def adaptive_threshold(gray: np.ndarray, block_size: int) -> np.ndarray:
    """
    Binarise ``gray`` with a mean adaptive threshold.

    The constant subtracted from the local mean (``C``) is increased step by
    step; the image kept is the last one produced before the foreground ratio
    drops noticeably, i.e. the strongest cleanup that does not erase text.
    """
    best_ratio = 0.0
    result = None

    for constant in range(1, 256):
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, block_size, constant,
        )
        foreground = cv2.countNonZero(binary)
        background = max(gray.size - foreground, 1)
        ratio = foreground / background

        best_ratio = max(best_ratio, ratio)
        if result is not None and ratio < RATIO_TOLERANCE * best_ratio:
            break
        result = binary

    return result
