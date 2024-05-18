from django.db import models

class Img(models.Model):
    ref=models.ImageField(null=True, upload_to="images")

class ExportedFile(models.Model):
    file = models.FileField(upload_to='exported_files', null=True)
    format = models.CharField(max_length=10)
    exported_at = models.DateTimeField(auto_now_add=True)