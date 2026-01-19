# Generated migration for OCR Settings

from django.db import migrations, models
import django.db.models.deletion
from pagewise.fields import ModelSeedSqidsField


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0004_enable_postgres_extensions'),
    ]

    operations = [
        # Create OcrSettings model
        migrations.CreateModel(
            name='OcrSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sqid', ModelSeedSqidsField(editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('name', models.CharField(default='default', max_length=100, unique=True)),
                ('ollama_base_url', models.CharField(default='http://localhost:11434', help_text='Ollama server URL for hosting PaddleOCR-VL', max_length=255)),
                ('paddleocr_model', models.CharField(default='paddleocr-vl', help_text='Name of the PaddleOCR-VL model in Ollama', max_length=100)),
                ('use_ocrmypdf', models.BooleanField(default=False, help_text='Apply OCRmyPDF to add selectable text to PDF')),
                ('ocrmypdf_language', models.CharField(default='eng', help_text='Language for OCRmyPDF (e.g., eng, deu, fra)', max_length=10)),
                ('ocrmypdf_compression', models.BooleanField(default=True, help_text='Enable compression in OCRmyPDF to reduce file size')),
                ('language', models.CharField(default='en', max_length=10)),
                ('settings_json', models.JSONField(blank=True, default=dict)),
            ],
            options={
                'verbose_name': 'OCR Settings',
                'verbose_name_plural': 'OCR Settings',
            },
        ),
        # Add ocr_settings field to Document
        migrations.AddField(
            model_name='document',
            name='ocr_settings',
            field=models.ForeignKey(blank=True, help_text='OCR settings for this document. If null, uses global default settings.', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='documents', to='documents.ocrsettings'),
        ),
        # Add ocrmypdf_applied field to Document
        migrations.AddField(
            model_name='document',
            name='ocrmypdf_applied',
            field=models.BooleanField(default=False, help_text='Whether OCRmyPDF has been applied to add selectable text to the PDF'),
        ),
        # Rename docling_layout to paddleocr_layout in Page
        migrations.RenameField(
            model_name='page',
            old_name='docling_layout',
            new_name='paddleocr_layout',
        ),
    ]
