from django.db import models
#from django.contrib.auths.models import user
# Create pytheo models here.
class Id(models.Model):
    doc=models.FileField(null=True)