# Generated manually - Remove Image model from documents app

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0008_alter_image_image_file'),
    ]

    operations = [
        # Remove Image model - it's been moved to the images app
        migrations.DeleteModel(
            name='Image',
        ),
    ]
