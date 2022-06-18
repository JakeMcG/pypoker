# Generated by Django 3.2 on 2022-06-18 18:53

from django.db import migrations
import core.interfaces.bcp as bcp

def fix_round(apps, schema):
    Action = apps.get_model("core", "Action")
    for a in Action.objects.all():
        a.round_new = bcp.ROUND_MAPPING[a.round]
        a.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0024_action_type_round'),
    ]

    operations = [
        migrations.RunPython(fix_round)
    ]