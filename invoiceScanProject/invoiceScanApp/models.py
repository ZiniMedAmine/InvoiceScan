from django.db import models

class Id(models.Model):
    doc=models.ImageField(null=True, upload_to="images")
 