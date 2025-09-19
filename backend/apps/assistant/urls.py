from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import command_view, execute_view, ConversationViewSet, MessageViewSet

router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'messages', MessageViewSet, basename='message')

urlpatterns = [
    path('command/', command_view, name='command'),
    path('execute/', execute_view, name='execute'),
    path('', include(router.urls)),
]


