import json
from datetime import datetime, timezone
from collections import OrderedDict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.apps import apps
from django.db.models import ForeignKey, OneToOneField, ManyToManyField, DateTimeField
from .models import Character, NPC, Quest

def clear_existing_character_creation_data(request):
    if 'character_creation' in request.session:
        del request.session['character_creation']
    request.session.modified = True

# New, modular initialize session data:

class CharacterInitializer:
    @staticmethod
    def initialize_basic_profile(character_name, existing_data=None):
        if existing_data is None:
            existing_data = {}

        return {
            "name": character_name,
            "race": existing_data.get('race', "Unknown"),
            "class": existing_data.get('class', "Unknown"),
            "subclass": existing_data.get('subclass', None),
            "discipline": existing_data.get('discipline', None),
            "ability_scores": existing_data.get('ability_scores', {
                "Strength": "Unknown",
                "Dexterity": "Unknown",
                "Constitution": "Unknown",
                "Intelligence": "Unknown",
                "Wisdom": "Unknown",
                "Charisma": "Unknown"
            }),
            "skills": existing_data.get('skills', ["Unknown"]),
            "hp": existing_data.get('hp', "Unknown"),
            "mp": existing_data.get('mp', None),
            "backstory": existing_data.get('backstory', "Unknown"),
            "last_updated": str(existing_data.get('last_updated', datetime.now(timezone.utc))),
            "version": existing_data.get('version', 0)
        }

    @staticmethod
    def initialize_inventory(existing_data=None):
        if existing_data is None:
            existing_data = {}

        return {
            "inventory": existing_data.get('inventory', {"items": ["A single grain of sand"]})
        }

    @staticmethod
    def initialize_zones(existing_data=None):
        if existing_data is None:
            existing_data = {}

        return {
            "starting_zone": existing_data.get('starting_zone', {
                "name": "Unknown",
                "description": "Unknown",
                "primary_races": ["Unknown"],
                "primary_classes": ["Unknown"],
                "last_updated": str(datetime.now(timezone.utc)),
                "version": 0
            }),
            "starting_subzone": existing_data.get('starting_subzone', {
                "name": "Unknown",
                "description": "Unknown",
                "primary_races": ["Unknown"],
                "primary_classes": ["Unknown"],
                "zone_id": "Unknown",
                "layout_description": "Unknown",
                "contained_objects": ["Unknown"]
            })
        }

    @staticmethod
    def initialize_character_creation_step(existing_data=None):
        if existing_data is None:
            existing_data = {}

        return {
            "character_creation_step": existing_data.get('character_creation_step', "building_basic_profile")
        }

    @staticmethod
    def initialize_conversation_history(existing_data=None):
        if existing_data is None:
            existing_data = {}

        return {
            "conversation_history": existing_data.get('conversation_history', [])
        }

    @staticmethod
    def initialize_game_state(existing_data=None):
        if existing_data is None:
            existing_data = {}
        return {
            "character_creation_step": existing_data.get('character_creation_step', "building_basic_profile"),
            "current_subzone": existing_data.get('current_subzone', "Unknown"),
            "npc_interaction": existing_data.get('npc_interaction', False),
            "exploring": existing_data.get('exploring', False),
            "conversation_history": existing_data.get('conversation_history', [])
        }

    @classmethod
    def initialize_character(cls, character_name, existing_data=None):
        character_data = {}
        character_data.update(cls.initialize_basic_profile(character_name, existing_data))
        character_data.update(cls.initialize_inventory(existing_data))
        character_data.update(cls.initialize_zones(existing_data))
        character_data.update(cls.initialize_character_creation_step(existing_data))
        character_data.update(cls.initialize_conversation_history(existing_data))
        return character_data
        
    # @staticmethod
#     def initialize_exploration(character_name):
#         try:
#             character = Character.objects.get(name=character_name)
#             return {
#                 "character_creation_step": "exploring_subzone",
#                 "current_subzone": character.location.name,
#                 "npc_interaction": False,
#                 "exploring": True,
#                 "player_character": {
#                     "name": character.name,
#                     "race": character.race,
#                     "char_class": character.char_class,
#                     "subclass": character.subclass,
#                     "discipline": character.discipline,
#                     "stats": character.stats,
#                     "skills": character.skills,
#                     "inventory": character.inventory,
#                     "hp": character.hp,
#                     "mp": character.mp,
#                     "backstory": character.backstory,
#                     "level": character.level,
#                     "xp": character.xp
#                 }
#             }
#         except Character.DoesNotExist:
#             return {
#                 "character_creation_step": "exploring_subzone",
#                 "current_subzone": "Unknown",
#                 "npc_interaction": False,
#                 "exploring": True,
#                 "player_character": {
#                     "name": "Unknown",
#                     "race": "Unknown",
#                     "char_class": "Unknown",
#                     "subclass": "Unknown",
#                     "discipline": "Unknown",
#                     "stats": {},
#                     "skills": [],
#                     "inventory": {},
#                     "hp": 0,
#                     "mp": 0,
#                     "backstory": "Unknown",
#                     "level": 1,
#                     "xp": 0
#                 }
#             }

    # @staticmethod
    # def initialize_starting_quest(character):
    #     try:
    #         initial_quest = Quest.objects.get(title="Starting Gear Quest")
    #         if not character.current_player_quests.filter(id=initial_quest.id).exists():
    #             character.current_player_quests.add(initial_quest)
    #             logger.info(f"Quest '{initial_quest.title}' added to character '{character.name}' current quests.")
    #         else:
    #             logger.info(f"Quest '{initial_quest.title}' already exists in character '{character.name}' current quests.")
    #         character.save()
    #     except Quest.DoesNotExist:
    #         logger.error("Initial quest does not exist. Please add it via admin.")
            
    @staticmethod
    def objective_met(objective, character):
        if objective['type'] == 'use_skill':
            return objective['skill'] in character.skills
        elif objective['type'] == 'collect_item':
            return character.inventory['items'].count(objective['item']) >= objective.get('quantity', 1)
        elif objective['type'] == 'defeat_enemy':
            return character.achievements.get('defeated_enemies', {}).get(objective['enemy'], 0) >= objective.get('quantity', 1)
        elif objective['type'] == 'interact_npc':
            return objective['npc'] in character.interacted_npcs
        elif objective['type'] == 'deliver_item':
            # Check if the character has interacted with the NPC and has the item
            has_item = character.inventory['items'].count(objective['item']) >= 1
            interacted_with_npc = objective['npc'] in character.interacted_npcs
            return has_item and interacted_with_npc
        return False

        
    # @staticmethod
    # def check_quest_completion(character):
    #     completed_player_quests = []
    #     rewards = {"items": [], "skills": [], "xp": 0}
    #
    #     for quest in character.current_player_quests.all():
    #         all_objectives_met = all(CharacterInitializer.objective_met(objective, character) for objective in quest.objectives)
    #         if all_objectives_met:
    #             completed_player_quests.append(quest)
    #             # Add quest rewards to character inventory, skills, and XP
    #             rewards["items"].extend(quest.rewards.get("items", []))
    #             rewards["skills"].extend(quest.rewards.get("skills", []))
    #             rewards["xp"] += quest.rewards.get("xp", 0)
    #             character.inventory["items"].extend(quest.rewards.get("items", []))
    #             character.skills.extend(quest.rewards.get("skills", []))
    #             character.xp += quest.rewards.get("xp", 0)
    #             character.completed_player_quests.add(quest)
    #             character.current_player_quests.remove(quest)
    #
    #     character.save()
    #     return completed_player_quests, rewards

# # don't think we're using this yet
# @csrf_exempt
# def handle_skill_use(request):
#     data = json.loads(request.body.decode('utf-8'))
#     character_name = data.get('character_name')
#     skill_used = data.get('skill_used')
#
#     if not character_name or not skill_used:
#         return JsonResponse({"error": "Character name and skill used are required."}, status=400)
#
#     try:
#         character = Character.objects.get(name=character_name)
#     except Character.DoesNotExist:
#         return JsonResponse({"error": f"Character '{character_name}' does not exist."}, status=404)
#
#     # Generate the static prompt for skill use
#     static_prompt = CharacterCreationPrompts.get_static_prompt_skill_use(character, skill_used)
#
#     # Send the prompt to the assistant
#     try:
#         assistant_message = create_completion([{"role": "system", "content": static_prompt}])
#     except Exception as e:
#         print(f"Error calling OpenAI API: {e}")
#         return JsonResponse({"error": "An error occurred while communicating with the AI."}, status=500)
#
#     # Extract skill use results and update quest status
#     character_creation = request.session.get('character_creation', {})
#     character_creation = extract_skill_use_and_update_quest(assistant_message, character_creation)
#     request.session['character_creation'] = character_creation
#     request.session.modified = True
#
#     return JsonResponse({"message": assistant_message, "character_creation": character_creation})
#
# # don't think we're using this yet
# def log_and_validate_skill_use(request, character, skill_used):
#     character_creation = request.session.get('character_creation', {})
#     skill_uses = character_creation.get('skill_uses', [])
#     skill_uses.append(skill_used)
#     character_creation['skill_uses'] = skill_uses
#     request.session['character_creation'] = character_creation
#     request.session.modified = True
#
#     # Validate quest objectives
#     completed_player_quests, rewards = CharacterInitializer.check_quest_completion(character)
#     quest_completion_messages = f"You have used the skill: {skill_used}."
#     if completed_player_quests:
#         quest_completion_messages += "\nYou have completed the following quests:\n"
#         for quest in completed_player_quests:
#             quest_completion_messages += f"- {quest.name}\n"
#             # Detailed rewards message
#             rewards_message = ""
#             if rewards['items']:
#                 rewards_message += f"Items: {', '.join(rewards['items'])}\n"
#             if rewards['xp']:
#                 rewards_message += f"XP: {rewards['xp']}\n"
#             if rewards['skills']:
#                 rewards_message += f"Skills: {', '.join(rewards['skills'])}\n"
#             quest_completion_messages += rewards_message
#
#     return {"message": quest_completion_messages}


def fetch_character_data_from_db(character):
    return {
        "name": character.name,
        "race": character.race,
        "class": character.char_class,
        "subclass": character.subclass,
        "discipline": character.discipline,
        "stats": character.stats,
        "skills": character.skills,
        "hp": character.hp,
        "mp": character.mp,
        "backstory": character.backstory,
        "inventory": character.inventory,
        "level": character.level,
        "xp": character.xp,
        "starting_zone": {
            "name": character.starting_zone.name,
            "description": character.starting_zone.description,
            "primary_races": list(character.starting_zone.primary_races),
            "primary_classes": list(character.starting_zone.primary_classes),
            "last_updated": str(character.starting_zone.last_updated),
        },
        "starting_subzone": {
            "name": character.starting_subzone.name,
            "description": character.starting_subzone.description,
            "primary_races": list(character.starting_subzone.primary_races),
            "primary_classes": list(character.starting_subzone.primary_classes),
        }
    }

def fetch_npc_data_from_db(subzone):
    npcs = NPC.objects.filter(current_subzone=subzone)
    npc_details = [
        {
            "name": npc.name,
            "race": npc.race,
            "backstory": npc.backstory,
            "description": npc.description,
            "demeanor": npc.demeanor,  # List field
            "can_train_in": npc.can_train_in,  # List field
            "gives_quests": list(npc.gives_quests.values_list('title', flat=True)),  # ManyToMany field, extracting quest titles
        }
        for npc in npcs
    ]
    return npc_details


@csrf_exempt
def delete_character(request, character_id):
    try:
        character = Character.objects.filter(id=character_id).first()
        if not character:
            return JsonResponse({"error": "Character not found"}, status=404)
        character.delete()
        return JsonResponse({"message": f"Character {character_id} deleted successfully"}, status=200)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred while deleting the character: {str(e)}"}, status=500)

@csrf_exempt
def list_characters(request):
    try:
        Character = apps.get_model('game', 'Character') 
        characters = Character.objects.all()
        character_list = []

        for character in characters:
            character_data = OrderedDict()
            for field in Character._meta.get_fields():
                field_name = field.name
                value = getattr(character, field_name, None)
                if isinstance(value, datetime):
                    value = value.isoformat()
                elif hasattr(value, 'id'):  # If the field is a related object, get its string representation
                    if field_name == 'location':
                        value = str(value)
                    elif field_name == 'starting_zone':
                        value = str(value)
                    elif field_name == 'starting_subzone':
                        value = str(value)
                    else:
                        value = value.id
                character_data[field_name] = value
            character_list.append(character_data)

        return JsonResponse(character_list, safe=False)
    except Exception as e:
        return JsonResponse({"error": f"An error occurred while listing characters: {str(e)}"}, status=500)
