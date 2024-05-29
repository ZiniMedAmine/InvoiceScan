from django.contrib import admin
from .models import Img, ExportedFile

# Register your models here.
class ImgAdmin(admin.ModelAdmin):
  list_display = ['ref','preprocessed_ref','extracted_text']

admin.site.register(Img, ImgAdmin)

class ExportedFileAdmin(admin.ModelAdmin):
  list_display = ['file', 'format', 'exported_at','img_id'] 

admin.site.register(ExportedFile, ExportedFileAdmin)