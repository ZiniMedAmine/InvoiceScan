from django.contrib import admin
from .models import Img, ExportedFile

# Register your models here.
class ImgAdmin(admin.ModelAdmin):
  list_display = ['ref']  # Fields to display in the admin list view

admin.site.register(Img, ImgAdmin)

class ExportedFileAdmin(admin.ModelAdmin):
  list_display = ['file', 'format', 'exported_at']  # Fields to display in the admin list view

admin.site.register(ExportedFile, ExportedFileAdmin)