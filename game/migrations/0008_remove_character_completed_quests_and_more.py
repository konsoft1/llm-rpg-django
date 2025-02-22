# Generated by Django 4.2.14 on 2024-07-31 21:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0007_character_completed_quests_character_current_quests'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='character',
            name='completed_quests',
        ),
        migrations.RemoveField(
            model_name='character',
            name='current_quests',
        ),
        migrations.AddField(
            model_name='character',
            name='completed_player_quests',
            field=models.ManyToManyField(blank=True, related_name='completed_player_quests', to='game.quest'),
        ),
        migrations.AddField(
            model_name='character',
            name='current_player_quests',
            field=models.ManyToManyField(blank=True, related_name='current_player_quests', to='game.quest'),
        ),
    ]
