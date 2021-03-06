# Generated by Django 3.2 on 2022-04-22 01:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_alter_hand_flop_cards'),
    ]

    operations = [
        migrations.AddField(
            model_name='seat',
            name='is_big_blind',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='seat',
            name='is_small_blind',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='seat',
            name='position',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='seat',
            name='is_winner',
            field=models.BooleanField(default=False),
        ),
    ]
