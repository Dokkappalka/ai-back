from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ImageGenerationViewSet,
    VideoGenerationViewSet,
    MusicGenerationViewSet,
    ConversationViewSet,
    MusicGenerationCallbackView,
    AvailableModelsView,
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'image', ImageGenerationViewSet, basename='image')
router.register(r'video', VideoGenerationViewSet, basename='video')
router.register(r'music', MusicGenerationViewSet, basename='music')
router.register(r'chat/conversations', ConversationViewSet, basename='conversation')

urlpatterns = [
    # Callback endpoint for Suno API (must be outside router as it's not a ViewSet)
    path('music/callback/', MusicGenerationCallbackView.as_view(), name='music-callback'),
    # Available AI models endpoint
    path('chat/models/', AvailableModelsView.as_view(), name='chat-models'),
    path('', include(router.urls)),
]
