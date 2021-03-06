# Generated by Django 3.2 on 2022-06-18 18:43

from django.db import migrations
import core.interfaces.bcp as bcp

# both round and type were previously stored based on BCP convention
def migrate_enums(apps, schema):
    Action = apps.get_model("core", "Action")
    for a in Action.objects.all():
        a.round_new = bcp.ROUND_MAPPING[a.round]
        a.type_new = bcp.ACTION_MAPPING[a.type]
        a.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0023_auto_20220618_1443'),
    ]

    operations = [
        migrations.RunPython(migrate_enums)
    ]
