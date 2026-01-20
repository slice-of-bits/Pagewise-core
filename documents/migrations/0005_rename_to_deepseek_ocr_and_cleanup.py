# Generated manually for renaming and cleanup

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0004_add_deepseek_ocr_support'),
    ]

    operations = [
        # Rename OCRSettings to DeepSeekOCRSettings
        migrations.RenameModel(
            old_name='OCRSettings',
            new_name='DeepSeekOCRSettings',
        ),
        
        # Remove legacy Docling fields from DeepSeekOCRSettings
        migrations.RemoveField(
            model_name='deepseekocrsettings',
            name='ocr_backend',
        ),
        migrations.RemoveField(
            model_name='deepseekocrsettings',
            name='ocr_engine',
        ),
        migrations.RemoveField(
            model_name='deepseekocrsettings',
            name='detect_tables',
        ),
        migrations.RemoveField(
            model_name='deepseekocrsettings',
            name='detect_figures',
        ),
        migrations.RemoveField(
            model_name='deepseekocrsettings',
            name='ignore_headers_footers',
        ),
        migrations.RemoveField(
            model_name='deepseekocrsettings',
            name='language',
        ),
        migrations.RemoveField(
            model_name='deepseekocrsettings',
            name='confidence_threshold',
        ),
        
        # Remove legacy docling_layout field from Page
        migrations.RemoveField(
            model_name='page',
            name='docling_layout',
        ),
        
        # Update bbox_visualization to use callable upload_to
        migrations.AlterField(
            model_name='page',
            name='bbox_visualization',
            field=models.FileField(blank=True, null=True, upload_to='documents.models.bbox_visualization_upload_path'),
        ),
        
        # Update meta options for DeepSeekOCRSettings
        migrations.AlterModelOptions(
            name='deepseekocrsettings',
            options={'verbose_name': 'DeepSeek OCR Settings', 'verbose_name_plural': 'DeepSeek OCR Settings'},
        ),
    ]
