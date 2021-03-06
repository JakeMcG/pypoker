# Generated by Django 3.2 on 2022-04-24 00:07

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_auto_20220421_2100'),
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.CharField(max_length=10)),
                ('amount', models.IntegerField(default=0)),
                ('round', models.CharField(max_length=20)),
                ('seat', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.seat')),
            ],
        ),
    ]
