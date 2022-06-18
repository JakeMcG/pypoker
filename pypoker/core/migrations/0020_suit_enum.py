# Generated by Django 3.2 on 2022-06-18 18:05

from django.db import migrations

def migrate_suit_enum(apps, schema):
    Card = apps.get_model("core", "PlayingCard")
    for c in Card.objects.all():
        c.suit_new = c.suit[0] # first character is key for enum
        c.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0019_playingcard_suit_new'),
    ]

    operations = [
        migrations.RunPython(migrate_suit_enum)
    ]