# Generated manually for deepseek-ocr integration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_enable_postgres_extensions'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='ocr_model',
            field=models.CharField(default='deepseek-ocr', max_length=100),
        ),
        migrations.AddField(
            model_name='page',
            name='ocr_references',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='page',
            name='bbox_visualization',
            field=models.FileField(blank=True, null=True, upload_to='bbox_visualizations/'),
        ),
        migrations.AddField(
            model_name='image',
            name='width',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='image',
            name='height',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RenameModel(
            old_name='DoclingSettings',
            new_name='OCRSettings',
        ),
        migrations.AddField(
            model_name='ocrsettings',
            name='ocr_backend',
            field=models.CharField(
                choices=[('deepseek-ocr', 'DeepSeek OCR'), ('docling', 'Docling (Legacy)')],
                default='deepseek-ocr',
                max_length=50
            ),
        ),
        migrations.AddField(
            model_name='ocrsettings',
            name='default_model',
            field=models.CharField(default='deepseek-ocr', max_length=100),
        ),
        migrations.AddField(
            model_name='ocrsettings',
            name='default_prompt',
            field=models.TextField(default='<|grounding|>Convert the document to markdown.'),
        ),
        migrations.AlterModelOptions(
            name='ocrsettings',
            options={'verbose_name': 'OCR Settings', 'verbose_name_plural': 'OCR Settings'},
        ),
    ]
