# Generated by Django 3.2 on 2022-07-16 19:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_auto_20220620_2001'),
    ]

    operations = [
        migrations.RenameField(
            model_name='hand',
            old_name='time_stamp',
            new_name='played_time',
        ),
    ]