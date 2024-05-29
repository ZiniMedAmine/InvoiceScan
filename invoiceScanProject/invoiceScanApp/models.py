# models.py

from django.db import models

class Img(models.Model):
    ref = models.ImageField(null=True, upload_to="images")
    preprocessed_ref = models.ImageField(null=True, upload_to="preprocessed_images")
    extracted_text = models.TextField(null=True, blank=True)

class ExportedFile(models.Model):
    file = models.FileField(upload_to='exported_files', null=True)
    format = models.CharField(max_length=10)
    exported_at = models.DateTimeField(auto_now_add=True)
    img_id = models.ForeignKey(Img, related_name='exported_files', on_delete=models.CASCADE, null=True, blank=True)
