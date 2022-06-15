# Generated by Django 3.2 on 2022-04-21 01:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0010_remove_table_site_key'),
    ]

    operations = [
        migrations.CreateModel(
            name='Seat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('hole_cards_shown', models.BooleanField(default=False)),
                ('is_winner', models.BooleanField()),
            ],
        ),
        migrations.RemoveField(
            model_name='hand',
            name='hero_win',
        ),
        migrations.RemoveField(
            model_name='hand',
            name='players',
        ),
        migrations.AddField(
            model_name='hand',
            name='flop_cards',
            field=models.ManyToManyField(null=True, related_name='flop_cards', to='core.PlayingCard'),
        ),
        migrations.AddField(
            model_name='hand',
            name='river_card',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='river_cards', to='core.playingcard'),
        ),
        migrations.AddField(
            model_name='hand',
            name='turn_card',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='turn_cards', to='core.playingcard'),
        ),
        migrations.DeleteModel(
            name='HoleCards',
        ),
        migrations.AddField(
            model_name='seat',
            name='hand',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.hand'),
        ),
        migrations.AddField(
            model_name='seat',
            name='hole_cards',
            field=models.ManyToManyField(to='core.PlayingCard'),
        ),
        migrations.AddField(
            model_name='seat',
            name='player',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.player'),
        ),
    ]
