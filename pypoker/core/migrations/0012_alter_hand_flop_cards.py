# Generated by Django 3.2 on 2022-04-21 01:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20220420_2142'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hand',
            name='flop_cards',
            field=models.ManyToManyField(to='core.PlayingCard'),
        ),
    ]
