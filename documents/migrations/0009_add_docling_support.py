# Generated manually for Docling integration

from django.db import migrations, models
import django.db.models.deletion
import documents.models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0008_alter_image_image_file'),
    ]

    operations = [
        # Create DoclingPreset model
        migrations.CreateModel(
            name='DoclingPreset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True, db_index=True)),
                ('name', models.CharField(max_length=100, unique=True, help_text='Preset name')),
                ('is_default', models.BooleanField(default=False, help_text='Set as default preset')),
                ('pipeline_type', models.CharField(
                    max_length=20,
                    choices=[('standard', 'Standard PDF Pipeline'), ('vlm', 'Vision-Language Model Pipeline')],
                    default='standard',
                    help_text='Pipeline type: standard PDF or VLM'
                )),
                ('ocr_engine', models.CharField(
                    max_length=20,
                    choices=[
                        ('auto', 'Auto (Best Available)'),
                        ('easyocr', 'EasyOCR'),
                        ('tesseract', 'Tesseract CLI'),
                        ('rapidocr', 'RapidOCR'),
                        ('ocrmac', 'macOS Vision OCR')
                    ],
                    default='auto',
                    help_text='OCR engine to use'
                )),
                ('force_ocr', models.BooleanField(default=False, help_text='Force full page OCR even for PDFs with text')),
                ('ocr_languages', models.JSONField(default=list, blank=True, help_text='List of language codes for OCR (format depends on OCR engine)')),
                ('vlm_model', models.CharField(max_length=200, blank=True, default='', help_text="VLM model repo ID (e.g., 'ibm-granite/granite-docling-258M')")),
                ('enable_picture_description', models.BooleanField(default=False, help_text='Generate descriptions for images using VLM')),
                ('picture_description_prompt', models.TextField(blank=True, default='Describe this image in a few sentences.', help_text='Prompt for picture description model')),
                ('enable_table_structure', models.BooleanField(default=True, help_text='Enable table structure extraction')),
                ('table_former_mode', models.CharField(
                    max_length=20,
                    choices=[('fast', 'Fast Mode'), ('accurate', 'Accurate Mode')],
                    default='accurate',
                    help_text='TableFormer extraction mode'
                )),
                ('enable_code_enrichment', models.BooleanField(default=False, help_text='Enable specialized processing for code blocks')),
                ('enable_formula_enrichment', models.BooleanField(default=False, help_text='Enable LaTeX formula recognition')),
                ('filter_orphan_clusters', models.BooleanField(default=False, help_text='Filter out orphaned text clusters (e.g., page numbers, headers)')),
                ('filter_empty_clusters', models.BooleanField(default=True, help_text='Filter out empty clusters in layout')),
                ('advanced_settings', models.JSONField(default=dict, blank=True, help_text='Advanced pipeline options in JSON format')),
            ],
            options={
                'verbose_name': 'Docling Preset',
                'verbose_name_plural': 'Docling Presets',
                'ordering': ['-is_default', 'name'],
            },
        ),
        
        # Add docling_json and docling_json_override fields to Page
        migrations.AddField(
            model_name='page',
            name='docling_json',
            field=models.JSONField(blank=True, null=True, help_text='Original docling JSON output'),
        ),
        migrations.AddField(
            model_name='page',
            name='docling_json_override',
            field=models.JSONField(blank=True, null=True, help_text='Corrected/overridden docling JSON data'),
        ),
        
        # Add docling_preset FK to Document
        migrations.AddField(
            model_name='document',
            name='docling_preset',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='documents',
                to='documents.doclingpreset',
                help_text='Docling preset to use for processing'
            ),
        ),
    ]
