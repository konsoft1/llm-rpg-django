# game/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import NPCViewSet

router = DefaultRouter()
router.register(r'npcs', NPCViewSet)

urlpatterns = [
    path('', views.index, name='index'),
    path('api/handle_character_creation', views.handle_character_creation, name='handle_character_creation'),
    path('api/delete_character/<int:character_id>', views.delete_character, name='delete_character'),
    path('api/list_characters', views.list_characters, name='list_characters'),
    path('api/initialize_exploration', views.initialize_exploration, name='initialize_exploration'),
    path('api/handle_skill_use', views.handle_skill_use_endpoint, name='handle_skill_use'),
]
