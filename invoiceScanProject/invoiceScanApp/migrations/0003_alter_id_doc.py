# Generated by Django 5.0.2 on 2024-03-09 00:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoiceScanApp', '0002_alter_id_doc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='id',
            name='doc',
            field=models.ImageField(null=True, upload_to='images'),
        ),
    ]
