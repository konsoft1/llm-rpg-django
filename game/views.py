import json
from datetime import datetime, timezone
from collections import OrderedDict
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import Character, Zone, Subzone, NPC, Quest
from .openai_client import create_completion
from .utils import clear_existing_character_creation_data, delete_character, list_characters, CharacterInitializer, fetch_character_data_from_db, fetch_npc_data_from_db
from .prompts import CharacterCreationPrompts
from .serializers import NPCSerializer
from rest_framework import viewsets

@csrf_exempt
def index(request):
    return render(request, 'game/index.html')

@csrf_exempt
def handle_character_creation(request):
    data = json.loads(request.body.decode('utf-8'))
    user_message = data.get('name') or data.get('message')
    print("Request data:", data)  # Debugging line
    print("User message:", user_message)  # Debugging line

    if not user_message:
        return JsonResponse({"error": "Please provide a character name or message."}, status=400)

    character_creation = request.session.get('character_creation', {})
    character_creation_step = character_creation.get('character_creation_step', 'choose_name')

    if data.get('name'):
        clear_existing_character_creation_data(request)
        character_name = user_message
        existing_character = Character.objects.filter(name=character_name).first()
        if existing_character:
            return JsonResponse({"message": f"The name '{character_name}' is already taken. Please choose a different name."}, status=400)
            
        # call initialize character to set up session data schema.
        initial_character_json = CharacterInitializer.initialize_character(character_name)
        
        request.session['character_creation'] = initial_character_json
        request.session.modified = True

        print(f"Character creation initialized for {character_name}.")
        return JsonResponse({"message": f"Great! What race would you like {character_name} to be?"})

    def save_character_to_db(character_creation):
        # Fetch the character if it exists or create a new one
        character_name = character_creation.get('name')
        character, created = Character.objects.get_or_create(name=character_name)

        # Update the character attributes (make sure the attribute names match your model)
        character.race = character_creation.get('race', character.race)
        character.char_class = character_creation.get('class', character.char_class)
        character.subclass = character_creation.get('subclass', character.subclass)
        character.discipline = character_creation.get('discipline', character.discipline)
        character.ability_scores = character_creation.get('ability_scores', character.stats)
        character.skills = character_creation.get('skills', character.skills)
        character.hp = character_creation.get('hp', character.hp)
        character.mp = character_creation.get('mp', character.mp)
        character.backstory = character_creation.get('backstory', character.backstory)
        character.last_updated = character_creation.get('last_updated', character.last_updated)
        character.version = character_creation.get('version', character.version)
        character.inventory = character_creation.get('inventory', character.inventory)
        character.level = character_creation.get('level', character.level)
        character.xp = character_creation.get('xp', character.xp)
    
        # Fetch the Zone instance
        starting_zone_data = character_creation.get('starting_zone')
        if starting_zone_data:
            starting_zone = Zone.objects.get(name=starting_zone_data['name'])
            character.starting_zone = starting_zone
    
        # Fetch the Subzone instance
        starting_subzone_data = character_creation.get('starting_subzone')
        if starting_subzone_data:
            starting_subzone = Subzone.objects.get(name=starting_subzone_data['name'])
            character.starting_subzone = starting_subzone
        
        # Fetch the current subzone
            current_subzone_data = character_creation.get('current_subzone', None)
            if isinstance(current_subzone_data, dict):
                current_subzone_name = current_subzone_data.get('name', '')
                current_subzone = Subzone.objects.get(name=current_subzone_name)
            elif isinstance(current_subzone_data, str):
                current_subzone = Subzone.objects.get(name=current_subzone_data)
            else:
                current_subzone = character.location
            character.location = current_subzone
        
        # Handle many-to-many fields
        current_player_quests_data = character_creation.get('current_player_quests', [])
        #if current_player_quests_data:
        current_player_quests = Quest.objects.filter(title__in=[quest['title'] for quest in current_player_quests_data])
        character.current_player_quests.set(current_player_quests)

        completed_player_quests_data = character_creation.get('completed_player_quests', [])
        if completed_player_quests_data:
            completed_player_quests = Quest.objects.filter(title__in=[quest['title'] for quest in completed_player_quests_data])
            character.completed_player_quests.set(completed_player_quests)
        
        character.conversation_history = character_creation.get('conversation_history', character.conversation_history)

        # Save the character
        character.save()
        print(f"Character '{character_name}' saved to the database. Created new: {created}")
        
    def extract_basic_character_info(message, character_creation):
        try:
            start_index = message.find('{')
            end_index = message.rfind('}') + 1
            if start_index == -1 or end_index == -1:
                raise ValueError("No JSON object found in the response")

            json_response = message[start_index:end_index]
            print(f"Extracted JSON response:\n {json_response}")
            response_data = json.loads(json_response)

            character_creation.update({
                'race': response_data.get('race', character_creation.get('race', 'Unknown')),
                'class': response_data.get('class', character_creation.get('class', 'Unknown')),
                'subclass': response_data.get('subclass', character_creation.get('subclass', 'Unknown')),
                'discipline': response_data.get('discipline', character_creation.get('discipline', 'Unknown')),
                'ability_scores': response_data.get('ability_scores', character_creation.get('ability_scores', {
                    "Strength": 'Unknown',
                    "Dexterity": 'Unknown',
                    "Constitution": 'Unknown',
                    "Intelligence": 'Unknown',
                    "Wisdom": 'Unknown',
                    "Charisma": 'Unknown'
                })),
                'skills': response_data.get('skills', character_creation.get('skills', ['Unknown'])),
                'hp': response_data.get('hp', character_creation.get('hp', 'Unknown')),
                'mp': response_data.get('mp', None),
                'backstory': response_data.get('backstory', character_creation.get('backstory', 'Unknown'))
            })

            required_fields = ['name', 'race', 'class', 'ability_scores', 'hp', 'skills', 'backstory']
            ability_scores = character_creation.get('ability_scores', {})
            skills = character_creation.get('skills', ['Unknown'])
            mp = character_creation.get('mp', None)

            if (
                all(field in character_creation for field in required_fields) and
                all(ability_scores.get(attr) != 'Unknown' for attr in ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']) and
                character_creation['hp'] != 'Unknown' and
                all(skill != 'Unknown' for skill in skills) and
                character_creation['backstory'] != 'Unknown' and
                (mp is None or mp != 'Unknown')
            ):
                character_creation['character_creation_step'] = 'confirm_basic_profile'
                request.session['character_creation'] = character_creation
                request.session.modified = True
                return {"character_creation_step": 'confirm_basic_profile'}
            else:
                missing_fields = [field for field in required_fields if character_creation.get(field, 'Unknown') == 'Unknown']
                if missing_fields:
                    return {"message": f"Please provide the following details: {', '.join(missing_fields)}"}

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error processing character info: {e}")

        return character_creation
        #end extract_basic_character_info
    
    def extract_zone_subzone_info(message, zone_creation):
        try:
            start_index = message.find('{')
            end_index = message.rfind('}') + 1
            if start_index == -1 or end_index == -1:
                raise ValueError("No JSON object found in the response")

            json_response = message[start_index:end_index]
            response_data = json.loads(json_response)

            # Extracting starting zone and subzone details
            starting_zone = response_data.get('starting_zone', {})
            starting_subzone = response_data.get('starting_subzone', {})
            existing_starting_zone = zone_creation.get('starting_zone', {})
            existing_starting_subzone = zone_creation.get('starting_subzone', {})

            zone_creation.update({
                'starting_zone': {
                    'name': starting_zone.get('name', existing_starting_zone.get('name', 'Unknown')),
                    'description': starting_zone.get('description', existing_starting_zone.get('description', 'Unknown')),
                    'primary_races': starting_zone.get('primary_races', existing_starting_zone.get('primary_races', ['Unknown'])),
                    'primary_classes': starting_zone.get('primary_classes', existing_starting_zone.get('primary_classes', ['Unknown'])),
                    'last_updated': str(datetime.now(timezone.utc)),
                    'version': 0
                },
                'starting_subzone': {
                    'name': starting_subzone.get('name', existing_starting_subzone.get('name', 'Unknown')),
                    'description': starting_subzone.get('description', existing_starting_subzone.get('description', 'Unknown')),
                    'primary_races': starting_subzone.get('primary_races', existing_starting_subzone.get('primary_races', ['Unknown'])),
                    'primary_classes': starting_subzone.get('primary_classes', existing_starting_subzone.get('primary_classes', ['Unknown'])),
                    'zone_id': starting_subzone.get('zone_id', existing_starting_subzone.get('zone_id', 'Unknown')),
                    'layout_description': starting_subzone.get('layout_description', existing_starting_subzone.get('layout_description', 'Unknown')),
                    'contained_objects': starting_subzone.get('contained_objects', existing_starting_subzone.get('contained_objects', ['Unknown']))
                }
            })

            required_fields = ['starting_zone', 'starting_subzone']
            if all(field in zone_creation for field in required_fields):
                zone_creation['character_creation_step'] = 'confirm_zone_creation'
                request.session['character_creation'] = zone_creation
                request.session.modified = True
                return {"character_creation_step": 'confirm_zone_creation'}
            else:
                missing_fields = [field for field in required_fields if zone_creation.get(field, 'Unknown') == 'Unknown']
                return {"message": f"Please provide the following details: {', '.join(missing_fields)}"}

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error processing zone info: {e}")

        return zone_creation
        
    def extract_exploring_subzone_info(character_creation, assistant_message):
        try:
            start_index = assistant_message.find('{')
            end_index = assistant_message.rfind('}') + 1
            if start_index == -1 or end_index == -1:
                raise ValueError("No JSON object found in the response")

            json_response = assistant_message[start_index:end_index]
            response_data = json.loads(json_response)

            character_creation.update({
                'name': response_data.get('player_character', {}).get('name', character_creation.get('name', 'Unknown')),
                'race': response_data.get('player_character', {}).get('race', character_creation.get('race', 'Unknown')),
                'class': response_data.get('player_character', {}).get('class', character_creation.get('class', 'Unknown')),
                'subclass': response_data.get('player_character', {}).get('subclass', character_creation.get('subclass', 'Unknown')),
                'discipline': response_data.get('player_character', {}).get('discipline', character_creation.get('discipline', 'Unknown')),
                'ability_scores': response_data.get('player_character', {}).get('stats', character_creation.get('ability_scores', {})),
                'skills': response_data.get('player_character', {}).get('skills', character_creation.get('skills', ['Unknown'])),
                'hp': response_data.get('player_character', {}).get('hp', character_creation.get('hp', 'Unknown')),
                'mp': response_data.get('player_character', {}).get('mp', None),
                'backstory': response_data.get('player_character', {}).get('backstory', character_creation.get('backstory', 'Unknown')),
                'inventory': response_data.get('player_character', {}).get('inventory', character_creation.get('inventory', {})),
                'level': response_data.get('player_character', {}).get('level', character_creation.get('level', 1)),
                'xp': response_data.get('player_character', {}).get('xp', 0),
                'starting_zone': response_data.get('zone', character_creation.get('starting_zone', {})),
                'starting_subzone': response_data.get('subzone', character_creation.get('starting_subzone', {})),
                'npcs': response_data.get('npcs', character_creation.get('npcs', [])),
                'current_player_quests': response_data.get('current_player_quests', character_creation.get('current_player_quests', [])),
            })

            # Check if 'current_player_quests' exists in response_data
            #
            # CURRENT ISSUE!
            #
            if 'current_player_quests' in response_data:
                print("Current player quests before processing:", response_data['current_player_quests'])

                # List to hold titles of completed quests
                completed_quest_titles = []

                # Iterate through current player quests
                for quest in response_data['current_player_quests']:
                    print("Processing quest:", quest)

                    # Ensure quest has a 'title' field
                    if 'title' not in quest:
                        print("Error: Quest is missing 'title' field:", quest)
                        continue  # Skip this quest if it doesn't have a 'title'

                    # Check if the quest is marked as complete
                    if quest.get('quest_complete', False):
                        print("Quest is complete:", quest)
                        # Append the quest title to completed_quest_titles
                        completed_quest_titles.append(quest['title'])

                # Update character_creation with completed quests
                character_creation['completed_player_quests'] = character_creation.get('completed_player_quests', []) + [
                    quest for quest in response_data['current_player_quests'] if quest['title'] in completed_quest_titles
                ]

                # Get the current quests
                current_quests = character_creation.get('current_player_quests', [])

                # Remove completed quests from current quests using their titles
                character_creation['current_player_quests'] = [quest for quest in current_quests if quest['title'] not in completed_quest_titles]

                # print("Character creation after processing:")
                print("Completed player quests:", character_creation['completed_player_quests'])
                print("Current player quests:", character_creation['current_player_quests'])

            # Ensure the session is updated with the latest state
            request.session['character_creation'] = character_creation
            request.session.modified = True

            print("Session data after update:", request.session['character_creation'])

            return character_creation

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error processing exploration subzone info: {e}")
            return character_creation

    if character_creation_step == 'building_basic_profile':
        conversation_history = character_creation.get('conversation_history', [])
        character_name = character_creation.get('name', 'Unknown')

        current_state_basic = CharacterInitializer.initialize_basic_profile(character_name, character_creation)
        
        # prompts from prompts.py
        static_prompt_basic_profile = CharacterCreationPrompts.get_static_prompt_basic_profile(character_name, current_state_basic)
        dynamic_message_basic_profile = CharacterCreationPrompts.get_dynamic_message_basic_profile(character_name, current_state_basic)

        messages = [{"role": "system", "content": static_prompt_basic_profile}] + [
            {"role": msg['role'], "content": msg['content']} for msg in conversation_history
        ]
        messages.append({"role": "user", "content": f"{user_message}\n\n{dynamic_message_basic_profile}"})

        print("Full prompt sent to OpenAI API:")
        for message in messages:
            print(f"{message['role']}:\n{message['content']}\n")

        try:
            assistant_message = create_completion(messages)
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return JsonResponse({"error": "An error occurred while communicating with the AI."}, status=500)

        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": assistant_message})

        print("Assistant's response:")
        print(assistant_message)

        character_creation['conversation_history'] = conversation_history
        extract_response = extract_basic_character_info(assistant_message, character_creation)
        request.session['character_creation'] = character_creation
        request.session.modified = True

        if extract_response.get('character_creation_step') == 'confirm_basic_profile':
            print("Character profile completed. Awaiting user confirmation.")
            character_creation['character_creation_step'] = 'confirm_basic_profile'  # Added this line
            request.session['character_creation'] = character_creation  # Moved this line here
            request.session.modified = True  # Moved this line here
            return JsonResponse({
                "message": f"{assistant_message}\n\nCharacter profile complete. Please confirm to proceed to zone creation.",
                "buttons": [
                    {"label": "Confirm", "value": "yes"}
                ]
            })

        request.session['character_creation'] = character_creation
        request.session.modified = True
        return JsonResponse({"message": assistant_message})

    if character_creation_step == 'confirm_basic_profile':
        if user_message.lower().strip() == 'yes':
            character_creation['character_creation_step'] = 'building_starting_zone'
            request.session['character_creation'] = character_creation
            request.session.modified = True
        
            matching_subzones = Subzone.objects.filter(
                primary_races__icontains=character_creation['race'],
                primary_classes__icontains=character_creation['class']
            )
        
            if matching_subzones.exists():
                subzone_options = [
                    {
                        "label": subzone.name,
                        "value": subzone.name,
                        "description": subzone.description,
                        "zone_name": subzone.zone.name,
                        "zone_description": subzone.zone.description
                    }
                    for subzone in matching_subzones
                ]
                subzone_messages = "\n\n".join([
                    f"**{option['label']}** - {option['description']}\n*Zone: {option['zone_name']}* - {option['zone_description']}"
                    for option in subzone_options
                ])
                return JsonResponse({
                    "message": f"Character profile confirmed. Now let's define the starting zone.\n\nHere are some matching starting subzones you can choose from:\n\n{subzone_messages}",
                    "buttons": [
                        {"label": option['label'], "value": option['value']} for option in subzone_options
                    ]
                })

            return JsonResponse({"message": "Character profile confirmed. Now let's define the starting zone."})

        else:
            conversation_history = character_creation.get('conversation_history', [])
            character_name = character_creation.get('name', 'Unknown')

            current_state_basic = CharacterInitializer.initialize_basic_profile(character_name, character_creation)
            
            # appropriate prompts from prompts.py
            static_prompt_basic_profile = CharacterCreationPrompts.get_static_prompt_basic_profile(character_name, current_state_basic)
            dynamic_message_basic_profile = CharacterCreationPrompts.get_dynamic_message_basic_profile(character_name, current_state_basic)

            messages = [{"role": "system", "content": static_prompt_basic_profile}] + [
                {"role": msg['role'], "content": msg['content']} for msg in conversation_history
            ]
            messages.append({"role": "user", "content": f"{user_message}\n\n{dynamic_message_basic_profile}"})

            print("Full prompt sent to OpenAI API:")
            for message in messages:
                print(f"{message['role']}:\n{message['content']}\n")

            try:
                assistant_message = create_completion(messages)
            except Exception as e:
                print(f"Error calling OpenAI API: {e}")
                return JsonResponse({"error": "An error occurred while communicating with the AI."}, status=500)

            conversation_history.append({"role": "user", "content": user_message})
            conversation_history.append({"role": "assistant", "content": assistant_message})

            print("Assistant's response:")
            print(assistant_message)

            character_creation['conversation_history'] = conversation_history
            extract_response = extract_basic_character_info(assistant_message, character_creation)
            request.session['character_creation'] = character_creation
            request.session.modified = True

            if extract_response.get('character_creation_step') == 'confirm_basic_profile':
                print("Character profile completed. Awaiting user confirmation.")
                return JsonResponse({
                    "message": f"{assistant_message}\n\nCharacter profile complete. Please CONFIRM to proceed to starting zone creation!",
                    "buttons": [
                        {"label": "Confirm", "value": "yes"}
                    ]
                })

            return JsonResponse({"message": assistant_message})
    
    # gets matched zone and subzone data for the session if needed
    def update_character_with_subzone(character_creation, subzone_name):
        subzone = Subzone.objects.get(name=subzone_name)
        zone = subzone.zone

        character_creation['starting_subzone'] = {
            'name': subzone.name,
            'description': subzone.description,
            'primary_races': subzone.primary_races,
            'primary_classes': subzone.primary_classes,
            'zone_id': subzone.zone.id,
            'layout_description': subzone.layout_description,
            'contained_objects': subzone.contained_objects
        }

        character_creation['starting_zone'] = {
            'name': zone.name,
            'description': zone.description,
            'primary_races': zone.primary_races,
            'primary_classes': zone.primary_classes,
            'zone_type': zone.zone_type,
            'last_updated': str(zone.last_updated),
            'version': zone.version
        }

        return character_creation


    if character_creation_step == 'building_starting_zone' or character_creation_step == 'confirm_zone_creation':
        print(f"Debug: Entered 'building_starting_zone' or 'confirm_zone_creation' step with message: {user_message}")
    
        # Check if the user confirms the zone creation
        if character_creation_step == 'confirm_zone_creation' and user_message.lower().strip() == 'yes':
            print("Debug: User confirmed character profile")
            # If the user confirms, save the character to the database
            save_response = save_character_to_db(character_creation)
            character_creation['character_creation_step'] = 'complete'
            request.session['character_creation'] = character_creation
            request.session.modified = True
            return JsonResponse({"message": f"Character profile confirmed and saved. {save_response['message']} Please start a new character creation process by refreshing the page and providing a new character name."})

        # Retrieve matching subzones
        matching_subzones = Subzone.objects.filter(
            primary_races__icontains=character_creation['race'],
            primary_classes__icontains=character_creation['class']
        )
        subzone_names = [subzone.name for subzone in matching_subzones]

        print(f"Debug: User message: {user_message}")  # Debugging statement
        print(f"Debug: Matching subzones: {subzone_names}")  # Debugging statement

        if user_message in subzone_names:
            print(f"Debug: User selected subzone: {user_message}")
            # If the user message matches a subzone name, update the session data
            character_creation = update_character_with_subzone(character_creation, user_message)
            request.session['character_creation'] = character_creation
            request.session.modified = True

            # Change character creation step to 'confirm_zone_creation'
            character_creation['character_creation_step'] = 'confirm_zone_creation'
            request.session['character_creation'] = character_creation
            request.session.modified = True

            # Prepare the JSON response with the necessary information
            response_data = {
                "message": "Character profile confirmed and saved with the selected subzone.",
                "buttons": [
                    {"label": "Confirm", "value": "yes"}
                ],
                "character_creation": character_creation
            }

            return JsonResponse(response_data)

        # Handle continuation of the normal conversation
        conversation_history = character_creation.get('conversation_history', [])
        character_name = character_creation.get('name', 'Unknown')
        character_race = character_creation.get('race', 'Unknown')
        char_class = character_creation.get('class', 'Unknown')
        character_backstory = character_creation.get('backstory', 'Unknown')

        # Create current_state_basic_zones
        basic_profile = CharacterInitializer.initialize_basic_profile(character_name, character_creation)
        zones = CharacterInitializer.initialize_zones(character_creation)
        current_state_basic_zones = {**basic_profile, **zones}

        static_prompt_starting_zone = CharacterCreationPrompts.get_static_prompt_starting_zone(character_name, character_race, char_class, character_backstory, current_state_basic_zones)
        dynamic_message_starting_zone = CharacterCreationPrompts.get_dynamic_message_starting_zone(current_state_basic_zones)

        messages = [{"role": "system", "content": static_prompt_starting_zone}] + [
            {"role": msg['role'], "content": msg['content']} for msg in conversation_history
        ]
        messages.append({"role": "user", "content": f"{user_message}\n\n{dynamic_message_starting_zone}"})

        print("Debug: Full prompt sent to OpenAI API:")
        for message in messages:
            print(f"Debug: {message['role']}:\n{message['content']}\n")

        try:
            assistant_message = create_completion(messages)
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return JsonResponse({"error": "An error occurred while communicating with the AI."}, status=500)

        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": assistant_message})

        print("Debug: Assistant's response:")
        print(assistant_message)

        character_creation['conversation_history'] = conversation_history
        extract_response = extract_zone_subzone_info(assistant_message, character_creation)
        request.session['character_creation'] = character_creation
        request.session.modified = True

        if extract_response.get('character_creation_step') == 'confirm_zone_creation':
            print("Debug: Zone creation completed. Awaiting user confirmation to save.")
            # Check for matching subzones
            matching_subzones = Subzone.objects.filter(
                primary_races__icontains=character_creation['race'],
                primary_classes__icontains=character_creation['class']
            )

            if matching_subzones.exists():
                subzone_options = [
                    {
                        "label": subzone.name,
                        "value": subzone.name,
                        "description": subzone.description,
                        "zone_name": subzone.zone.name,
                        "zone_description": subzone.zone.description
                    }
                    for subzone in matching_subzones
                ]
                subzone_messages = "\n\n".join([
                    f"**{option['label']}** - {option['description']}\n*Zone: {option['zone_name']}* - {option['zone_description']}"
                    for option in subzone_options
                ])
                assistant_message += f"\n\nHere are some matching starting subzones you can choose from:\n\n{subzone_messages}"
                buttons = [{"label": option['label'], "value": option['value']} for option in subzone_options]

                # Append both confirm and subzone options buttons
                buttons.append({"label": "Confirm", "value": "yes"})

                return JsonResponse({
                    "message": f"{assistant_message}\n\nZone creation complete. Please confirm to save the character or choose a subzone.",
                    "buttons": buttons
                })

            return JsonResponse({
                "message": f"{assistant_message}\n\nZone creation complete. Please confirm to save the character.",
                "buttons": [
                    {"label": "Confirm", "value": "yes"}
                ]
            })

        return JsonResponse({"message": assistant_message})

    if character_creation_step == 'exploring_subzone':
        print("Current step: exploring_subzone")
        character_name = character_creation.get('name', 'Unknown')
        current_subzone_name = character_creation.get('current_subzone', 'Unknown')
        current_subzone = Subzone.objects.get(name=current_subzone_name)
        current_zone = current_subzone.zone
        npc_interaction = character_creation.get('npc_interaction', False)
        exploring = character_creation.get('exploring', True)
        conversation_history = character_creation.get('conversation_history', [])

        # Fetch NPCs in the current subzone
        npcs = fetch_npc_data_from_db(current_subzone)

        # Fetch character data
        character_data = Character.objects.get(name=character_name)

        # Fetch quests related to the character
        current_player_quests = character_data.current_player_quests.all()
        completed_player_quests = character_data.completed_player_quests.all()

        # Generate static and dynamic prompts for exploration
        static_prompt_exploration = CharacterCreationPrompts.get_exploration_prompt(
            current_subzone, current_zone, npcs, character_data, current_player_quests
        )
        dynamic_message_exploration = CharacterCreationPrompts.get_dynamic_message_exploration(
            character_data, current_subzone, npcs
        )

        # Combine exploration and quest prompts
        messages = [{"role": "system", "content": static_prompt_exploration}] + [
            {"role": msg['role'], "content": msg['content']} for msg in conversation_history
        ]
        messages.append({"role": "user", "content": f"{user_message}\n\n{dynamic_message_exploration}"})

        print("Full prompt sent to OpenAI API:")
        for message in messages:
            print(f"{message['role']}:\n{message['content']}\n")

        # Log the initial character creation state before any updates are applied
        initial_character_creation_state = character_creation.copy()
        # print(f"Initial character creation state: {initial_character_creation_state}")

        try:
            assistant_message = create_completion(messages)
        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return JsonResponse({"error": "An error occurred while communicating with the AI."}, status=500)

        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": assistant_message})

        print("Assistant's response:")
        print(assistant_message)

        # Extract data and update character state
        new_character_creation = extract_exploring_subzone_info(character_creation, assistant_message)

        # Log the new character creation state after extraction
        print(f"Character creation state after extraction: {new_character_creation}")

        # Check for differences and save if there are any changes
        if new_character_creation != initial_character_creation_state:
            print("Changes detected. Saving to DB...")
            save_character_to_db(new_character_creation)
            character_creation = new_character_creation
        else:
            print("No changes detected. Skipping save.")

        request.session['character_creation'] = character_creation
        request.session.modified = True

        # Fetch updated character data from the database after the assistant response
        character_data = Character.objects.get(name=character_name)

        return JsonResponse({
            "message": assistant_message,
            "character_creation": fetch_character_data_from_db(character_data),  # Send the updated character state back to the front end
            "npcs": npcs,  # include npcs data
            "current_player_quests": [{"title": quest.title} for quest in character_data.current_player_quests.all()]  # include current player quests
        })


@csrf_exempt
def initialize_exploration(request):
    data = json.loads(request.body.decode('utf-8'))
    character_name = data.get('name')

    if not character_name:
        return JsonResponse({"error": "Please provide a character name."}, status=400)

    existing_character = Character.objects.filter(name=character_name).first()
    if not existing_character:
        return JsonResponse({"error": f"No character found with the name '{character_name}'."}, status=404)

    # Initialize the session data
    character_creation = CharacterInitializer.initialize_character(character_name)
    character_creation['current_subzone'] = existing_character.location.name
    character_creation['character_creation_step'] = 'exploring_subzone'
    character_creation['conversation_history'] = []

    request.session['character_creation'] = character_creation
    request.session['character_id'] = existing_character.id
    request.session.modified = True

    character_data = fetch_character_data_from_db(existing_character)

    return JsonResponse({
        "message": f"Character '{character_name}' loaded and ready to explore the subzone '{existing_character.location.name}'.",
        "character_creation": character_creation,
        "character_data": character_data
    })

def extract_exploration_info(message, character_creation, request):
    try:
        start_index = message.find('{')
        end_index = message.rfind('}') + 1
        if start_index == -1 or end_index == -1:
            raise ValueError("No JSON object found in the response")

        json_response = message[start_index:end_index]
        response_data = json.loads(json_response)

        character_creation.update({
            'current_subzone': response_data.get('current_subzone', character_creation.get('current_subzone', {})),
            'npc_interaction': response_data.get('npc_interaction', character_creation.get('npc_interaction', False)),
            'exploring': response_data.get('exploring', character_creation.get('exploring', True)),
            'conversation_history': character_creation.get('conversation_history', [])
        })

        required_fields = ['current_subzone', 'npc_interaction', 'exploring']
        if all(field in character_creation for field in required_fields):
            character_creation['character_creation_step'] = 'exploring_subzone'
            request.session['character_creation'] = character_creation
            request.session.modified = True
            return {"character_creation_step": 'exploring_subzone'}
        else:
            missing_fields = [field for field in required_fields if character_creation.get(field, 'Unknown') == 'Unknown']
            return {"message": f"Please provide the following details: {', '.join(missing_fields)}"}

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error processing exploration info: {e}")

    return character_creation


# # I think this is not in use
# def extract_skill_use_and_update_quest(message, character_creation):
#     try:
#         start_index = message.find('{')
#         end_index = message.rfind('}') + 1
#         if start_index == -1 or end_index == -1:
#             raise ValueError("No JSON object found in the response")
#
#         json_response = message[start_index:end_index]
#         response_data = json.loads(json_response)
#
#         # Update skill use results
#         skill_check = response_data.get('skill_check', {})
#         if skill_check:
#             character_creation['last_skill_used'] = skill_check
#
#         # Update quest statuses
#         quest_updates = response_data.get('quest_status', {})
#         if quest_updates:
#             for quest in character_creation.get('current_player_quests', []):
#                 if quest['title'] == quest_updates['quest_name']:
#                     for objective in quest['objectives']:
#                         if objective['description'] == quest_updates['objective']:
#                             objective['completed'] = quest_updates['completed']
#
#         return character_creation
#
#     except (json.JSONDecodeError, ValueError) as e:
#         print(f"Error processing skill use and quest updates: {e}")
#
#     return character_creation


@csrf_exempt
def handle_skill_use_endpoint(request):
    return handle_skill_use(request)
 
# NPCs!
class NPCViewSet(viewsets.ModelViewSet):
    queryset = NPC.objects.all()
    serializer_class = NPCSerializer
