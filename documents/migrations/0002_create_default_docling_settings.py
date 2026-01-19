# Generated manually

from django.db import migrations


def create_default_settings(apps, schema_editor):
    DoclingSettings = apps.get_model('documents', 'DoclingSettings')
    DoclingSettings.objects.get_or_create(
        name='default',
        defaults={
            'ocr_engine': 'tesseract',
            'detect_tables': True,
            'detect_figures': True,
            'ignore_headers_footers': True,
            'language': 'en',
            'confidence_threshold': 0.7,
        }
    )


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_settings, migrations.RunPython.noop),
    ]

