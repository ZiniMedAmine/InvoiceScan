from django.contrib import admin

from .models import ExportedFile, ScannedDocument


class ExportedFileInline(admin.TabularInline):
    model = ExportedFile
    extra = 0
    readonly_fields = ["file", "format", "exported_at"]


@admin.register(ScannedDocument)
class ScannedDocumentAdmin(admin.ModelAdmin):
    list_display = ["id", "filename", "document_type", "uploaded_at"]
    list_filter = ["document_type"]
    search_fields = ["image", "document_type", "extracted_text"]
    readonly_fields = ["uploaded_at"]
    inlines = [ExportedFileInline]


@admin.register(ExportedFile)
class ExportedFileAdmin(admin.ModelAdmin):
    list_display = ["file", "format", "document", "exported_at"]
    list_filter = ["format"]
