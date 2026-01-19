# Migration to replace Ollama/PaddleOCR-VL with Marker PDF

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0006_create_default_ocr_settings'),
    ]

    operations = [
        # Remove Ollama-specific fields from OcrSettings
        migrations.RemoveField(
            model_name='ocrsettings',
            name='ollama_base_url',
        ),
        migrations.RemoveField(
            model_name='ocrsettings',
            name='paddleocr_model',
        ),
        # Add Marker-specific fields
        migrations.AddField(
            model_name='ocrsettings',
            name='force_ocr',
            field=models.BooleanField(default=False, help_text='Force OCR on all pages, even those with existing text'),
        ),
        # Rename paddleocr_layout to marker_layout in Page model
        migrations.RenameField(
            model_name='page',
            old_name='paddleocr_layout',
            new_name='marker_layout',
        ),
    ]
