"""
WebSocket URL routing for API app.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/music/updates/$', consumers.MusicGenerationConsumer.as_asgi()),
]

