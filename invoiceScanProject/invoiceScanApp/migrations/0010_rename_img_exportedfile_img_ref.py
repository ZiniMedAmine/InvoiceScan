# Generated by Django 5.0.2 on 2024-05-29 09:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('invoiceScanApp', '0009_exportedfile_img'),
    ]

    operations = [
        migrations.RenameField(
            model_name='exportedfile',
            old_name='img',
            new_name='img_ref',
        ),
    ]
