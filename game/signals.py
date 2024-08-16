import logging
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from .models import Character

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

@receiver(m2m_changed, sender=Character.current_player_quests.through)
def log_current_player_quests_change(sender, instance, action, **kwargs):
    if action in ['post_add', 'post_remove', 'post_clear']:
        logger.info(f"Action: {action} - Character: {instance.name} - Current Player Quests: {[quest.title for quest in instance.current_player_quests.all()]}")