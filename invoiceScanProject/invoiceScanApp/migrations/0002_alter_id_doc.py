# Generated by Django 5.0.2 on 2024-03-08 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoiceScanApp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='id',
            name='doc',
            field=models.ImageField(null=True, upload_to=''),
        ),
    ]
