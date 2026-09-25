import csv
import io
import json
import zipfile

from django.test import SimpleTestCase

from invoiceScanApp.services.exporters import flatten, to_csv, to_docx, to_json

DATA = {
    "Invoice Number": "F-001",
    "Client": {"Name": "Société ACME", "City": "Tunis"},
    "Items": {"1": {"Label": "Paper", "Price": 12.5}},
}


class FlattenTests(SimpleTestCase):
    def test_nested_dicts_and_lists(self):
        self.assertEqual(
            dict(flatten({"a": {"b": 1}, "c": [2, {"d": 3}]})),
            {"a.b": 1, "c.0": 2, "c.1.d": 3},
        )


class ExporterTests(SimpleTestCase):
    def test_json(self):
        self.assertEqual(json.loads(to_json("Invoice", DATA)), DATA)

    def test_csv(self):
        rows = list(csv.reader(io.StringIO(to_csv("Invoice", DATA).decode("utf-8-sig"))))
        self.assertEqual(rows[0], ["field", "value"])
        self.assertEqual(rows[1], ["document_type", "Invoice"])
        self.assertIn(["Client.Name", "Société ACME"], rows)
        self.assertIn(["Items.1.Price", "12.5"], rows)

    def test_docx(self):
        content = to_docx("Invoice", DATA)
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            body = archive.read("word/document.xml").decode("utf-8")
        self.assertIn("Société ACME", body)
        self.assertIn("Items", body)
