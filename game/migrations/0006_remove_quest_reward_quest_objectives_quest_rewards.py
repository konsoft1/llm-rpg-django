# Generated by Django 4.2.14 on 2024-07-31 02:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0005_alter_subzone_zone_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='quest',
            name='reward',
        ),
        migrations.AddField(
            model_name='quest',
            name='objectives',
            field=models.JSONField(default=dict),
        ),
        migrations.AddField(
            model_name='quest',
            name='rewards',
            field=models.JSONField(default=dict),
        ),
    ]
