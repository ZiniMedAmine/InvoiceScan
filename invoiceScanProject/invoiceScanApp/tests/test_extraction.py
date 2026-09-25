import json

from django.test import SimpleTestCase

from invoiceScanApp.services.extraction import UNKNOWN_DOCUMENT_TYPE, parse_model_response


class ParseModelResponseTests(SimpleTestCase):
    def test_parses_markdown_answer(self):
        answer = (
            "*Document Type: Invoice*\n\n"
            "```json\n"
            '{"Invoice Number": "F-2024-001", "Total": {"Amount": 120.5, "Currency": "TND"}}\n'
            "```\n"
        )

        result = parse_model_response(answer)

        self.assertEqual(result.document_type, "Invoice")
        self.assertEqual(
            json.loads(result.json_text),
            {"Invoice Number": "F-2024-001", "Total": {"Amount": 120.5, "Currency": "TND"}},
        )

    def test_keeps_accented_document_types(self):
        result = parse_model_response("Document Type: Facture d'électricité\n{}")
        self.assertEqual(result.document_type, "Facture d'électricité")

    def test_missing_document_type(self):
        result = parse_model_response('{"a": 1}')
        self.assertEqual(result.document_type, UNKNOWN_DOCUMENT_TYPE)

    def test_invalid_json_is_returned_as_is_for_manual_fix(self):
        result = parse_model_response('*Document Type: Receipt*\n{"a": 1,}')
        self.assertEqual(result.document_type, "Receipt")
        self.assertEqual(result.json_text, '{"a": 1,}')

    def test_answer_without_json(self):
        result = parse_model_response("Sorry, I cannot read this document.")
        self.assertEqual(result.json_text, "Sorry, I cannot read this document.")
