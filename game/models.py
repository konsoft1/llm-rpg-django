from django.db import models
from datetime import datetime
from django.utils import timezone

class Zone(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField()
    primary_races = models.JSONField(default=list)
    primary_classes = models.JSONField(default=list)
    zone_type = models.CharField(max_length=80, null=True, blank=True)
    last_updated = models.DateTimeField(default=timezone.now)
    version = models.IntegerField(default=0)

    def __str__(self):
        return self.name

class Subzone(models.Model):
    name = models.CharField(max_length=80, unique=True)
    description = models.TextField()
    primary_races = models.JSONField(default=list)
    primary_classes = models.JSONField(default=list)
    zone_type = models.JSONField(default=list, null=True, blank=True)
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='subzones')
    layout_description = models.TextField(null=True, blank=True)
    contained_objects = models.JSONField(null=True, blank=True)
    last_updated = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

class Character(models.Model):
    name = models.CharField(max_length=80, unique=True)
    race = models.CharField(max_length=80)
    char_class = models.CharField(max_length=80)
    subclass = models.CharField(max_length=80, null=True, blank=True)
    discipline = models.CharField(max_length=80, null=True, blank=True)
    stats = models.JSONField(default=dict)  # Default to an empty dictionary
    skills = models.JSONField(default=list)  # Default to an empty dictionary
    inventory = models.JSONField(default=dict)  # Default to an empty dictionary
    location = models.ForeignKey('Subzone', on_delete=models.SET_NULL, null=True, blank=True, related_name='characters')
    starting_zone = models.ForeignKey('Zone', on_delete=models.SET_NULL, null=True, blank=True, related_name='characters_starting')
    starting_subzone = models.ForeignKey('Subzone', on_delete=models.SET_NULL, null=True, blank=True, related_name='characters_starting')
    last_updated = models.DateTimeField(default=timezone.now)
    version = models.IntegerField(default=0)
    hp = models.IntegerField()
    mp = models.IntegerField(null=True, blank=True)
    backstory = models.TextField(null=True, blank=True)
    level = models.IntegerField(null=True, blank=True, default=1)  # Ensure default level is 1
    xp = models.IntegerField(null=True, blank=True, default=0)  # Ensure default XP is 0
    current_player_quests = models.ManyToManyField('Quest', related_name='current_player_quests', blank=True)
    completed_player_quests = models.ManyToManyField('Quest', related_name='completed_player_quests', blank=True)
    conversation_history = models.JSONField(default=list)  # New field
    # not in use yet... will add skill proficiency bonus later
    # @property
    # def skill_proficiency_bonus(self):
    #     if self.level >= 17:
    #         return 6
    #     elif self.level >= 13:
    #         return 5
    #     elif self.level >= 9:
    #         return 4
    #     elif self.level >= 5:
    #         return 3
    #     else:
    #         return 2
    #
    # def __str__(self):
    #     return self.name


class Quest(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    objectives = models.JSONField(default=dict)  # E.g., {"collect_item": "Grain of Sand"}
    rewards = models.JSONField(default=dict)  # E.g., {"items": ["Starter Sword"], "xp": 100}

    def __str__(self):
        return self.title


class NPC(models.Model):
    name = models.CharField(max_length=80, unique=True)
    race = models.CharField(max_length=50)
    char_class = models.CharField(max_length=50)
    subclass = models.CharField(max_length=50, null=True, blank=True)
    current_subzone = models.ForeignKey(Subzone, on_delete=models.SET_NULL, null=True, blank=True)
    backstory = models.TextField(null=True, blank=True)
    description = models.TextField()
    demeanor = models.JSONField(default=list)  # List of attributes like 'talkative', 'grim', etc.
    skills = models.JSONField(default=list)
    can_train_in = models.JSONField(default=list)
    gives_quests = models.ManyToManyField('Quest', blank=True)
    inventory = models.JSONField(default=dict)

    def __str__(self):
        return self.name





