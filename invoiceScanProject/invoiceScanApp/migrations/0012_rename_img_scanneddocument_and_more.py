"""Give the models and fields descriptive names and record document metadata."""

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("invoiceScanApp", "0011_rename_img_ref_exportedfile_img_id"),
    ]

    operations = [
        migrations.RenameModel(old_name="Img", new_name="ScannedDocument"),
        migrations.RenameField(
            model_name="scanneddocument",
            old_name="ref",
            new_name="image",
        ),
        migrations.RenameField(
            model_name="scanneddocument",
            old_name="preprocessed_ref",
            new_name="preprocessed_image",
        ),
        migrations.RenameField(
            model_name="exportedfile",
            old_name="img_id",
            new_name="document",
        ),
        migrations.AddField(
            model_name="scanneddocument",
            name="document_type",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
        migrations.AddField(
            model_name="scanneddocument",
            name="uploaded_at",
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="exportedfile",
            name="format",
            field=models.CharField(
                choices=[("json", "JSON"), ("csv", "CSV"), ("word", "Word")],
                max_length=10,
            ),
        ),
        migrations.AlterModelOptions(
            name="scanneddocument",
            options={"ordering": ["-uploaded_at"]},
        ),
        migrations.AlterModelOptions(
            name="exportedfile",
            options={"ordering": ["-exported_at"]},
        ),
    ]
