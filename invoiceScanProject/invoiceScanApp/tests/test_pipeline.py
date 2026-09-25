import shutil
import tempfile
from unittest import mock

import cv2
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings

from invoiceScanApp.services.extraction import ExtractionError, ExtractionResult
from invoiceScanApp.services.pipeline import scan_document

from .test_preprocessing import make_document_image

MEDIA_ROOT = tempfile.mkdtemp()


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ScanDocumentTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def upload(self):
        _, data = cv2.imencode(".jpg", make_document_image())
        return SimpleUploadedFile("invoice.jpg", data.tobytes(), content_type="image/jpeg")

    @mock.patch("invoiceScanApp.services.pipeline.structure_text")
    @mock.patch("invoiceScanApp.services.pipeline.extract_text", return_value="INVOICE N 42")
    def test_runs_every_step_and_saves_the_result(self, extract_text, structure_text):
        structure_text.return_value = ExtractionResult("Invoice", '{"Number": 42}')

        document = scan_document(self.upload())

        extract_text.assert_called_once()
        structure_text.assert_called_once_with("INVOICE N 42")
        document.refresh_from_db()
        self.assertEqual(document.document_type, "Invoice")
        self.assertEqual(document.extracted_text, '{"Number": 42}')
        self.assertTrue(document.preprocessed_image.name.endswith(".png"))

    def test_undecodable_image_raises_extraction_error(self):
        broken = SimpleUploadedFile("broken.jpg", b"garbage", content_type="image/jpeg")
        with self.assertRaises(ExtractionError):
            scan_document(broken)
