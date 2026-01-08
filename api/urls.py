from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ImageGenerationViewSet,
    VideoGenerationViewSet,
    MusicGenerationViewSet,
    ChatMessageViewSet,
    MusicGenerationCallbackView,
)

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'image', ImageGenerationViewSet, basename='image')
router.register(r'video', VideoGenerationViewSet, basename='video')
router.register(r'music', MusicGenerationViewSet, basename='music')
router.register(r'chat', ChatMessageViewSet, basename='chat')

urlpatterns = [
    # Callback endpoint for Suno API (must be outside router as it's not a ViewSet)
    # IMPORTANT: keep this BEFORE router URLs so that /api/music/callback/
    # is not captured by the "music" viewset detail route (pk='callback').
    path('music/callback/', MusicGenerationCallbackView.as_view(), name='music-callback'),
    path('', include(router.urls)),
]

