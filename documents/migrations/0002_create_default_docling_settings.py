# Generated migration to create default Docling settings

from django.db import migrations

def create_default_docling_settings(apps, schema_editor):
    """Create default Docling settings via data migration."""
    DoclingSettings = apps.get_model('documents', 'DoclingSettings')

    # Create default settings if they don't exist
    if not DoclingSettings.objects.filter(name='default').exists():
        DoclingSettings.objects.create(
            name='default',
            ocr_engine='tesseract',
            detect_tables=True,
            detect_figures=True,
            ignore_headers_footers=True,
            language='en',
            confidence_threshold=0.7,
            settings_json={
                'preprocessing': {
                    'rotate_pages': True,
                    'denoise': False,
                    'enhance_contrast': False
                },
                'postprocessing': {
                    'remove_duplicates': True,
                    'merge_fragments': True,
                    'preserve_both_formats': True  # Always generate both markdown and JSON
                },
                'output_config': {
                    'generate_markdown': True,
                    'generate_json': True,
                    'markdown_for_search': True,
                    'json_for_structure': True
                }
            }
        )

def reverse_default_docling_settings(apps, schema_editor):
    """Remove default Docling settings."""
    DoclingSettings = apps.get_model('documents', 'DoclingSettings')
    DoclingSettings.objects.filter(name='default').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_default_docling_settings,
            reverse_default_docling_settings,
            atomic=True,
        ),
    ]
