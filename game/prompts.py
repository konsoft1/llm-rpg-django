import json

class CharacterCreationPrompts:
    
    # 1. basic character info prompt
    
    @staticmethod
    def get_static_prompt_basic_profile(character_name, current_state_basic):
        return (
            f"You are an expert D&D 5e DM and character creation assistant. "
            f"Help the character, {character_name}, go through each step of the character creation process. "
            f"Ask them to choose their own character details (class, ability scores, skills), and make helpful suggestions and/or rolls as needed, always remembering to include the important facts (e.g., how many skills one can choose from, etc.).\n"
            f"Note that the game has some differences to actual D&D 5e, e.g.:\n"
            f" 1. Additional races and classes can be created on the fly, and you will help make them logical.\n"
            f" That said, if they are trying to make up a new race or class that sounds like an existing one, steer them into the existing analogous race or class.\n"
            f" 2. *Spellcasting players only* will also use Mana Points (MP) instead of spell slots (not applicable to non-spellcasters, so just skip this if not relevant). You will help them set their MP just like HP. Starting MP will be based on a 1d10 roll plus an intelligence modifier, instead of a constitution modifier, to determine MP.\n"
            f"Finally, **always** send back the updated character profile with every message based on the latest message using this exact JSON schema/model:\n\n"
            f"{json.dumps(current_state_basic, indent=2)}"
        )

    @staticmethod
    def get_dynamic_message_basic_profile(character_name, current_state_basic):
        return (
            f"(Again **ALWAYS** update the character details for {character_name} accordingly, and send the latest JSON object containing the info you have so far, using the format and fields provided):\n\n"
            f"{json.dumps(current_state_basic, indent=2)}"
        )
        
    # 2. prompt for creating/choosing starting zone and subzone

    @staticmethod
    def get_static_prompt_starting_zone(character_name, character_race, character_class, character_backstory, current_state_full):
        return (
            f"Generate a creative but relevant starting zone and subzone for the character {character_name} to start playing the game in. "
            f"The 'starting subzone' is the specific starting area itself (e.g., a training ground, academy, dojo, workshop, library, arena, etc.). "
            f"The 'starting zone' is the larger area that the subzone is found in (e.g., a city, forest, treetop village, castle, cave network, etc.). "
            f"Consider all character details like their race ({character_race}), class ({character_class}), and backstory ({character_backstory}) when creating. "
            f"And again, be creative and dynamic in the description and details! "
            f"Use this exact JSON schema to populate the starting zone profile:\n\n"
            f"{json.dumps(current_state_full, indent=2)}\n\n"
        )

    
    def get_dynamic_message_exploration(player_character, subzone, npcs):
        return ""    

    
    def get_exploring_subzone_basic_prompt(subzone, zone, npcs, character, quests):
        def pretty_json(data):
            return json.dumps(data, indent=4, separators=(',', ': '))

        return f"""
You are a Dungeon Master (DM) and you will also role-play any Non-Player Characters (NPCs) present in the scene.
You will greet the player, introduce them to the current subzone, and chat about relevant things, any notable features, and any other NPCs present.
You will also respond as the NPCs if the player interacts with them.

Here is the current game state:

{{
  "player_character": {{
    "name": "{character.name}",
    "race": "{character.race}",
    "class": "{character.char_class}",
    "subclass": "{character.subclass}",
    "discipline": "{character.discipline}",
    "stats": {pretty_json(character.stats)},
    "skills": {pretty_json(character.skills)},
    "hp": {character.hp},
    "mp": {character.mp},
    "backstory": "{character.backstory}",
    "inventory": {pretty_json(character.inventory)},
    "level": {character.level},
    "xp": {character.xp}
  }},
  "subzone": {{
    "name": "{subzone.name}",
    "description": "{subzone.description}",
    "primary_races": {pretty_json(subzone.primary_races)},
    "primary_classes": {pretty_json(subzone.primary_classes)},
    "zone_id": "{subzone.zone.id}",
    "layout_description": "{subzone.layout_description}",
    "contained_objects": {pretty_json(subzone.contained_objects)}
  }},
  "zone": {{
    "name": "{zone.name}",
    "description": "{zone.description}",
    "primary_races": {pretty_json(zone.primary_races)},
    "primary_classes": {pretty_json(zone.primary_classes)},
    "zone_type": "{zone.zone_type}",
    "last_updated": "{zone.last_updated}",
    "version": {zone.version}
  }},
  "npcs": {pretty_json(npcs)},
  "current_player_quests": {pretty_json([{
    "title": quest.title,
    "description": quest.description,
    "objectives": quest.objectives,
    "rewards": quest.rewards,
    "quest_complete": False
  } for quest in quests]) if quests else 'None'}
}}
"""

    def get_exploring_subzone_active_quest_prompt(character, active_quest):
        return f"""
**Note for for the Assistant:** The character {character.name} has an active quest: {active_quest.title}!

As the Dungeon Master (DM) you will:

- Assist and motivate the player in completing their quest using creative methods and prompts (e.g., talk to a certain NPC, mention a note on a table, etc., etc.)
- Always require the player to roll for the skill check, tell them what the difficulty level is, and don't forget to apply any modifiers to the skill check!
- You will also continue to create and act as Non-Player Characters (NPCs), some of which might be helpful in completing the quest (some might not be helpful!)
- Remember what the quest objective is and acknowledge when the quest is complete based on the player actions (e.g., a successful skill use, defeating a foe, giving an item to an NPC, etc.). Use your amazing inference capabilities to judge this.

Here is the currently active player quest again for reference:

- Quest "title": {active_quest.title}
- Quest "type": {active_quest.objectives[0]['type']}
- Quest "objective": {active_quest.objectives[0]['description']}.

**Important*: When the character completes the requirements of the quest, return the game state json object, leaving the data in the current_player_quests key, but update the `False` value to `True`
**Please be sure to *always, always provide the **full game state JSON response at the end of every response you send (no exceptions).**
"""
# Use the skill: "{active_quest.objectives[0]['skill']}" to complete the task.

    def get_exploration_prompt(subzone, zone, npcs, character, quests):
        exploration_prompt = CharacterCreationPrompts.get_exploring_subzone_basic_prompt(subzone, zone, npcs, character, quests)
        if character.current_player_quests.exists():
            active_quest = character.current_player_quests.first()
            quest_prompt = CharacterCreationPrompts.get_exploring_subzone_active_quest_prompt(character, active_quest)
            return exploration_prompt + quest_prompt
        return exploration_prompt
    
    
    @staticmethod
    def get_static_prompt_skill_use(character, skill):
        return (
            f"You are a Dungeon Master (DM) guiding the player through their quest. "
            f"The character {character['name']} is attempting to use the skill {skill}. "
            f"Evaluate the skill use attempt, narrate the outcome, and provide feedback on the character's progress. "
            f"Update the quest status based on the skill use attempt.\n\n"
            f"Please use the following JSON schema to update the game state with the skill check result:\n\n"
            f"{{\n"
            f"  \"skill_check\": {{\n"
            f"    \"skill\": \"{skill}\",\n"
            f"    \"success\": true/false,\n"
            f"    \"details\": \"Describe the outcome of the skill use.\"\n"
            f"  }},\n"
            f"  \"quest_status\": {{\n"
            f"    \"quest_name\": \"{character['current_player_quests'][0]['name'] if character['current_player_quests'] else 'No active quest'}\",\n"
            f"    \"objective\": \"{character['current_player_quests'][0]['objectives'][0]['description'] if character['current_player_quests'] else 'No active quest'}\",\n"
            f"    \"completed\": true/false,\n"
            f"    \"details\": \"Describe the progress of the quest based on the skill use.\"\n"
            f"  }}\n"
            f"}}\n\n"
            f"Current character details:\n"
            f"{json.dumps(character, indent=2)}"
        )

    @staticmethod
    def get_dynamic_message_skill_use(character, skill):
        return (
            f"The character {character['name']} is using the skill {skill}. "
            f"Update the game state accordingly and provide feedback on the character's progress.\n\n"
            f"Here is the current game state:\n"
            f"{{\n"
            f"  \"skill_check\": {{\n"
            f"    \"skill\": \"{skill}\",\n"
            f"    \"success\": true/false,\n"
            f"    \"details\": \"Describe the outcome of the skill use.\"\n"
            f"  }},\n"
            f"  \"quest_status\": {{\n"
            f"    \"quest_name\": \"{character['current_player_quests'][0]['name'] if character['current_player_quests'] else 'No active quest'}\",\n"
            f"    \"objective\": \"{character['current_player_quests'][0]['objectives'][0]['description'] if character['current_player_quests'] else 'No active quest'}\",\n"
            f"    \"completed\": true/false,\n"
            f"    \"details\": \"Describe the progress of the quest based on the skill use.\"\n"
            f"  }}\n"
            f"}}\n\n"
            f"{json.dumps(character, indent=2)}"
        )
    