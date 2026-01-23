# Generated migration for renaming groups to ponds

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ponds', '0001_initial'),
        ('documents', '0009_add_docling_support'),  # Latest documents migration
    ]

    operations = [
        # Rename the Group model to Pond
        migrations.RenameModel(
            old_name='Group',
            new_name='Pond',
        ),
        # Rename the GroupShare model to PondShare
        migrations.RenameModel(
            old_name='GroupShare',
            new_name='PondShare',
        ),
        # Update the foreign key field name in PondShare
        migrations.RenameField(
            model_name='pondshare',
            old_name='group',
            new_name='pond',
        ),
    ]
