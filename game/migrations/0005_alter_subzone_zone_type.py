# Generated by Django 4.2.14 on 2024-07-30 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0004_quest_npc'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subzone',
            name='zone_type',
            field=models.JSONField(blank=True, default=list, null=True),
        ),
    ]
