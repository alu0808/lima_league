# matches/migrations/0006_backfill_match_identifier_and_set_default.py
from django.db import migrations, models
import uuid

def backfill_match_identifier(apps, schema_editor):
    Match = apps.get_model('matches', 'Match')
    for m in Match.objects.filter(match_identifier__isnull=True):
        m.match_identifier = uuid.uuid4()
        m.save(update_fields=['match_identifier'])

class Migration(migrations.Migration):

    dependencies = [
        ('matches', '0005_match_match_identifier'),
    ]

    operations = [
        migrations.RunPython(backfill_match_identifier, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='match',
            name='match_identifier',
            field=models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True),
        ),
    ]
