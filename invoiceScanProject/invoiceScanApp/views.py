"""
HTTP views of InvoiceScan+.

User flow:

1. ``home``: upload one or more document images, which are scanned right away.
2. ``review``: read and optionally edit the JSON extracted from each document.
3. ``save_edited_text``: persist the (possibly edited) JSON.
4. ``export_data``: download the data as JSON / CSV / Word files in a ZIP.

The documents of the current scan are remembered in the user's session, so a
visitor can only review and export the documents they uploaded themselves.
"""

import io
import json
import zipfile

from django.core.files.base import ContentFile
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import UploadForm
from .models import ExportedFile, ScannedDocument
from .services.exporters import EXPORT_FORMATS
from .services.extraction import ExtractionError
from .services.pipeline import scan_document

SESSION_KEY = "scanned_document_ids"
EXPORT_ARCHIVE_NAME = "invoicescan_export.zip"


def home(request):
    """Landing page with the upload form; scans the images on submit."""
    if request.method == "POST":
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                documents = [scan_document(file) for file in form.cleaned_data["files"]]
            except ExtractionError as exc:
                form.add_error(None, str(exc))
            else:
                request.session[SESSION_KEY] = [document.pk for document in documents]
                return redirect("review")
    else:
        form = UploadForm()

    return render(request, "invoiceScanApp/home.html", {"form": form})


def review(request):
    """Show the extracted data of the current scan so the user can edit it."""
    documents = _session_documents(request)
    if not documents:
        return redirect("home")
    return render(request, "invoiceScanApp/review.html", {"documents": documents})


@require_POST
def save_edited_text(request):
    """
    Save the JSON of each document after the user reviewed it.

    Expected body: ``[{"id": <document id>, "text": "<JSON string>"}, ...]``.
    Nothing is saved unless every submitted text is a valid JSON object.
    """
    payload = _parse_json_body(request)
    if not isinstance(payload, list):
        return _error("Expected a list of documents.")

    documents = {document.pk: document for document in _session_documents(request)}
    updated = []
    for item in payload:
        document = documents.get(item.get("id")) if isinstance(item, dict) else None
        if document is None:
            return _error("Unknown document.")
        text = item.get("text")
        try:
            data = json.loads(text) if isinstance(text, str) else None
        except json.JSONDecodeError as exc:
            return _error(f"{document.filename}: invalid JSON ({exc}).")
        if not isinstance(data, dict):
            return _error(f"{document.filename}: the data must be a JSON object.")
        document.extracted_text = text
        updated.append(document)

    ScannedDocument.objects.bulk_update(updated, ["extracted_text"])
    return JsonResponse({"status": "success"})


@require_POST
def export_data(request):
    """
    Export the documents of the current scan as a ZIP archive.

    Expected body: ``{"formats": ["json", "csv", "word"]}`` (any subset).
    Each generated file is also stored and recorded as an ``ExportedFile``.
    """
    payload = _parse_json_body(request)
    formats = payload.get("formats") if isinstance(payload, dict) else None
    valid = isinstance(formats, list) and formats and all(
        isinstance(key, str) and key in EXPORT_FORMATS for key in formats
    )
    if not valid:
        return _error(f"Choose at least one format among: {', '.join(EXPORT_FORMATS)}.")
    formats = list(dict.fromkeys(formats))  # drop duplicates, keep order

    documents = _session_documents(request)
    if not documents:
        return _error("There is nothing to export, please upload documents first.")

    parsed = []
    for document in documents:
        try:
            parsed.append((document, json.loads(document.extracted_text or "")))
        except json.JSONDecodeError:
            return _error(f"{document.filename}: fix the JSON before exporting.")

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for document, data in parsed:
            for format_key in formats:
                export_format = EXPORT_FORMATS[format_key]
                filename = f"{document.stem}.{export_format.extension}"
                content = export_format.render(document.document_type, data)

                zip_file.writestr(filename, content)
                exported = ExportedFile(document=document, format=format_key)
                exported.file.save(filename, ContentFile(content))

    response = HttpResponse(archive.getvalue(), content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="{EXPORT_ARCHIVE_NAME}"'
    return response


def _session_documents(request) -> list[ScannedDocument]:
    """Documents uploaded by the current visitor in their latest scan."""
    ids = request.session.get(SESSION_KEY, [])
    return list(ScannedDocument.objects.filter(pk__in=ids).order_by("pk"))


def _parse_json_body(request):
    try:
        return json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None


def _error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"status": "error", "message": message}, status=status)
