# Create default OCR settings

from django.db import migrations


def create_default_ocr_settings(apps, schema_editor):
    OcrSettings = apps.get_model('documents', 'OcrSettings')
    OcrSettings.objects.get_or_create(
        name='default',
        defaults={
            'ollama_base_url': 'http://localhost:11434',
            'paddleocr_model': 'paddleocr-vl',
            'use_ocrmypdf': False,
            'ocrmypdf_language': 'eng',
            'ocrmypdf_compression': True,
            'language': 'en',
            'settings_json': {},
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0005_add_ocr_settings_model'),
    ]

    operations = [
        migrations.RunPython(create_default_ocr_settings, migrations.RunPython.noop),
    ]
