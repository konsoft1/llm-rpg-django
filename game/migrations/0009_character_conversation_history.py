# Generated by Django 4.2.14 on 2024-08-01 04:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0008_remove_character_completed_quests_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='character',
            name='conversation_history',
            field=models.JSONField(default=list),
        ),
    ]
