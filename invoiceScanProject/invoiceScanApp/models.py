"""Database models of the InvoiceScan+ application."""

from pathlib import Path

from django.db import models


class ScannedDocument(models.Model):
    """An uploaded document image and the data extracted from it."""

    image = models.ImageField(upload_to="images", null=True)
    preprocessed_image = models.ImageField(upload_to="preprocessed_images", null=True)
    document_type = models.CharField(max_length=255, blank=True, default="")
    # JSON produced by Gemini, possibly corrected by the user on the review page.
    extracted_text = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return self.filename or f"Document #{self.pk}"

    @property
    def filename(self) -> str:
        """Name of the uploaded image file, without its storage folder."""
        return Path(self.image.name).name if self.image else ""

    @property
    def stem(self) -> str:
        """Base name used for exported files (e.g. ``invoice_01``)."""
        return Path(self.image.name).stem if self.image else f"document_{self.pk}"


class ExportedFile(models.Model):
    """A file generated when the user exports a document's data."""

    class Format(models.TextChoices):
        JSON = "json", "JSON"
        CSV = "csv", "CSV"
        WORD = "word", "Word"

    document = models.ForeignKey(
        ScannedDocument,
        related_name="exported_files",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    file = models.FileField(upload_to="exported_files", null=True)
    format = models.CharField(max_length=10, choices=Format.choices)
    exported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-exported_at"]

    def __str__(self) -> str:
        return Path(self.file.name).name if self.file else f"Export #{self.pk}"
