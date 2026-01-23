# Generated migration for renaming group field to pond in documents

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ponds', '0002_rename_groups_to_ponds'),
        ('documents', '0009_add_docling_support'),
    ]

    operations = [
        # Rename the foreign key field from group to pond
        migrations.RenameField(
            model_name='document',
            old_name='group',
            new_name='pond',
        ),
        # Update the foreign key to point to ponds.Pond instead of groups.Group
        migrations.AlterField(
            model_name='document',
            name='pond',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='documents',
                to='ponds.pond'
            ),
        ),
    ]
