import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'llm_rpg.settings')
django.setup()

from game.models import Character

# Prompt the user for character ID or name
character_input = input("Please enter the character ID or name: ")

try:
    # Determine if the input is an ID (numeric) or a name (string)
    if character_input.isdigit():
        character = Character.objects.get(id=character_input)
    else:
        # Convert input to lowercase for case-insensitive matching
        character_input = character_input.lower()
        # Use a case-insensitive query to get the character by name
        character = Character.objects.get(name__iexact=character_input)

    # Collect character data
    character_data = {
        'name': character.name,
        'race': character.race,
        'class': character.char_class,
        'subclass': character.subclass,
        'discipline': character.discipline,
        'stats': character.stats,
        'skills': character.skills,
        'hp': character.hp,
        'mp': character.mp,
        'backstory': character.backstory,
        'inventory': character.inventory,
        'level': character.level,
        'xp': character.xp,
        'starting_zone': character.starting_zone.name if character.starting_zone else None,
        'starting_subzone': character.starting_subzone.name if character.starting_subzone else None,
        'location': character.location.name if character.location else None,
        'last_updated': character.last_updated,
        'version': character.version,
        'current_player_quests': [
            f"{quest.title} (ID {quest.id})" for quest in character.current_player_quests.all()
        ],
        'completed_player_quests': [
            f"{quest.title} (ID {quest.id})" for quest in character.completed_player_quests.all()
        ],
    }

    # Print the character data
    for key, value in character_data.items():
        print(f"{key}: {value}")

except Character.DoesNotExist:
    print(f"Character with ID or name '{character_input}' does not exist.")