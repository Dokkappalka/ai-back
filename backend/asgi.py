"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

# Initialize Django ASGI application early to ensure the AppRegistry
# is populated before importing code that may import ORM models.
django_asgi_app = get_asgi_application()

# Wrap with WhiteNoise for serving static files in ASGI mode
# (WhiteNoise WSGI middleware doesn't work with uvicorn/ASGI)
from django.conf import settings
from whitenoise import WhiteNoise
django_asgi_app = WhiteNoise(django_asgi_app, root=str(settings.STATIC_ROOT), prefix="/static/")

# Import routing after Django is initialized
from api import routing

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            routing.websocket_urlpatterns
        )
    ),
})

