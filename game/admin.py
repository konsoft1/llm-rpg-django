from django.contrib import admin
from django.contrib.sessions.models import Session
from django.utils.html import format_html
from django.utils import timezone
from .models import Character, Zone, Subzone, NPC, Quest

class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'race', 'char_class', 'level')
    readonly_fields = ('current_player_quests_display', 'completed_player_quests_display')

    def current_player_quests_display(self, obj):
        current_quests = obj.current_player_quests.all()
        if current_quests.exists():
            return format_html('<ul>{}</ul>', format_html(''.join([f'<li>{quest.title}</li>' for quest in current_quests])))
        return 'No current quests'
    current_player_quests_display.short_description = 'Current Quests'

    def completed_player_quests_display(self, obj):
        completed_quests = obj.completed_player_quests.all()
        if completed_quests.exists():
            return format_html('<ul>{}</ul>', format_html(''.join([f'<li>{quest.title}</li>' for quest in completed_quests])))
        return 'No completed quests'
    completed_player_quests_display.short_description = 'Completed Quests'

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('current_player_quests', 'completed_player_quests')

    fieldsets = (
        (None, {
            'fields': (
                'name', 'race', 'char_class', 'subclass', 'discipline', 'stats', 'skills', 
                'inventory', 'location', 'starting_zone', 'starting_subzone', 'last_updated', 
                'version', 'hp', 'mp', 'backstory', 'level', 'xp', 
                'current_player_quests',  # Make this field editable
                'completed_player_quests',  # Make this field editable
                'current_player_quests_display', 
                'completed_player_quests_display'
            )
        }),
    )

    filter_horizontal = ('current_player_quests', 'completed_player_quests')  # Ensure better UI

admin.site.register(Character, CharacterAdmin)
admin.site.register(Zone)
admin.site.register(Subzone)
admin.site.register(NPC)
admin.site.register(Quest)

class SessionAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'session_data_display', 'expire_date', 'is_expired']
    readonly_fields = ['session_key', 'session_data_display', 'expire_date']

    def is_expired(self, obj):
        return obj.expire_date < timezone.now()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'

    def session_data_display(self, obj):
        data = obj.get_decoded()
        return format_html('<pre>{}</pre>', data)
    session_data_display.short_description = 'Session Data'

admin.site.register(Session, SessionAdmin)