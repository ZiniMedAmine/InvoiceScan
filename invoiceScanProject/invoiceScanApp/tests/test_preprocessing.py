import cv2
import numpy as np
from django.test import SimpleTestCase

from invoiceScanApp.services.preprocessing import (
    BORDER_SIZE,
    UPSCALE_FACTOR,
    encode_png,
    load_image,
    preprocess_image,
    round_to_odd,
)


def make_document_image() -> np.ndarray:
    """White page with a few lines of black text."""
    image = np.full((200, 400, 3), 255, np.uint8)
    for line, text in enumerate(["INVOICE N 42", "Total: 120.500 TND", "Tunis 2024"]):
        cv2.putText(image, text, (10, 40 + line * 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
    return image


class PreprocessingTests(SimpleTestCase):
    def test_round_to_odd(self):
        self.assertEqual([round_to_odd(v) for v in (2, 4.9, 6.1, 7, 10)], [3, 5, 7, 7, 11])

    def test_output_is_upscaled_padded_binary_image(self):
        result = preprocess_image(make_document_image())

        expected_shape = (200 * UPSCALE_FACTOR + 2 * BORDER_SIZE, 400 * UPSCALE_FACTOR + 2 * BORDER_SIZE)
        self.assertEqual(result.shape, expected_shape)
        self.assertTrue(set(np.unique(result)) <= {0, 255})

    def test_blank_page_does_not_hang(self):
        blank = np.full((100, 100, 3), 255, np.uint8)
        self.assertIsNotNone(preprocess_image(blank))

    def test_png_round_trip(self):
        image = make_document_image()
        self.assertTrue(np.array_equal(load_image(encode_png(image)), image))

    def test_load_image_rejects_non_images(self):
        with self.assertRaises(ValueError):
            load_image(b"not an image")
