import io
import json
import shutil
import tempfile
import zipfile
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from invoiceScanApp.models import ExportedFile, ScannedDocument
from invoiceScanApp.services.extraction import ExtractionError
from invoiceScanApp.views import SESSION_KEY

MEDIA_ROOT = tempfile.mkdtemp()


def png_upload(name="invoice.png"):
    buffer = io.BytesIO()
    Image.new("RGB", (10, 10), "white").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=MEDIA_ROOT)
class ViewTestCase(TestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(MEDIA_ROOT, ignore_errors=True)

    def create_document(self, text='{"Total": 10}'):
        return ScannedDocument.objects.create(
            image=png_upload(), document_type="Invoice", extracted_text=text,
        )

    def start_session(self, *documents):
        session = self.client.session
        session[SESSION_KEY] = [document.pk for document in documents]
        session.save()

    def post_json(self, url_name, payload):
        return self.client.post(reverse(url_name), json.dumps(payload), content_type="application/json")


class HomeViewTests(ViewTestCase):
    def test_get(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Upload Your Images")

    def test_upload_scans_files_and_redirects_to_review(self):
        document = self.create_document()
        with mock.patch("invoiceScanApp.views.scan_document", return_value=document) as scan:
            response = self.client.post(reverse("home"), {"files": [png_upload()]})

        self.assertRedirects(response, reverse("review"))
        scan.assert_called_once()
        self.assertEqual(self.client.session[SESSION_KEY], [document.pk])

    def test_rejects_non_image_files(self):
        fake = SimpleUploadedFile("notes.png", b"not an image", content_type="image/png")
        with mock.patch("invoiceScanApp.views.scan_document") as scan:
            response = self.client.post(reverse("home"), {"files": [fake]})

        self.assertEqual(response.status_code, 200)
        scan.assert_not_called()
        self.assertTrue(response.context["form"].errors)

    def test_shows_extraction_errors(self):
        with mock.patch("invoiceScanApp.views.scan_document", side_effect=ExtractionError("AI down")):
            response = self.client.post(reverse("home"), {"files": [png_upload()]})
        self.assertContains(response, "AI down")


class ReviewViewTests(ViewTestCase):
    def test_redirects_home_without_scan(self):
        self.assertRedirects(self.client.get(reverse("review")), reverse("home"))

    def test_lists_session_documents(self):
        document = self.create_document('{"Total": 99}')
        self.start_session(document)

        response = self.client.get(reverse("review"))

        self.assertContains(response, "Document Type: Invoice")
        self.assertContains(response, "&quot;Total&quot;: 99")


class SaveEditedTextTests(ViewTestCase):
    def test_saves_valid_json(self):
        document = self.create_document()
        self.start_session(document)

        response = self.post_json("save_edited_text", [{"id": document.pk, "text": '{"Total": 20}'}])

        self.assertEqual(response.status_code, 200)
        document.refresh_from_db()
        self.assertEqual(document.extracted_text, '{"Total": 20}')

    def test_rejects_invalid_json_without_saving(self):
        document = self.create_document()
        self.start_session(document)

        response = self.post_json("save_edited_text", [{"id": document.pk, "text": "{oops"}])

        self.assertEqual(response.status_code, 400)
        document.refresh_from_db()
        self.assertEqual(document.extracted_text, '{"Total": 10}')

    def test_cannot_edit_documents_of_another_session(self):
        document = self.create_document()
        response = self.post_json("save_edited_text", [{"id": document.pk, "text": "{}"}])
        self.assertEqual(response.status_code, 400)

    def test_requires_post(self):
        self.assertEqual(self.client.get(reverse("save_edited_text")).status_code, 405)


class ExportDataTests(ViewTestCase):
    def test_exports_selected_formats_as_zip(self):
        document = self.create_document()
        self.start_session(document)

        response = self.post_json("export_data", {"formats": ["json", "csv", "word"]})

        self.assertEqual(response["Content-Type"], "application/zip")
        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
            names = sorted(archive.namelist())
        self.assertEqual(names, sorted(f"{document.stem}.{ext}" for ext in ("json", "csv", "docx")))
        self.assertEqual(ExportedFile.objects.filter(document=document).count(), 3)

    def test_rejects_unknown_format(self):
        self.start_session(self.create_document())
        response = self.post_json("export_data", {"formats": ["pdf"]})
        self.assertEqual(response.status_code, 400)

    def test_rejects_invalid_stored_json(self):
        self.start_session(self.create_document("{oops"))
        response = self.post_json("export_data", {"formats": ["json"]})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(ExportedFile.objects.exists())
