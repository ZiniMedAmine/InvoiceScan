"""
Business logic of InvoiceScan+, kept independent from the HTTP layer.

- ``preprocessing``: OpenCV image cleanup before OCR.
- ``ocr``: text recognition with Tesseract.
- ``extraction``: document classification and JSON structuring with Gemini.
- ``pipeline``: runs the three steps above on an uploaded file.
- ``exporters``: JSON / CSV / Word file generation.
"""
