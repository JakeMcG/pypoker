# Generated by Django 3.2 on 2022-06-18 18:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0025_fix_round_enum'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='action',
            name='round',
        ),
        migrations.RemoveField(
            model_name='action',
            name='type',
        ),
    ]
