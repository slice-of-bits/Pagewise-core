# Generated manually

from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_create_default_docling_settings'),
    ]

    operations = [
        TrigramExtension(),
    ]

