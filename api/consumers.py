"""
WebSocket consumers for real-time updates.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings

logger = logging.getLogger(__name__)


class MusicGenerationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for music generation updates.
    Authenticates users via JWT token from query parameters.
    """

    async def connect(self):
        print("Connecting to WebSocket")
        """
        Handle WebSocket connection.
        Authenticates user via JWT token from query parameters.
        """
        # Extract token from query parameters
        token = self.scope.get('query_string', b'').decode('utf-8')
        
        # Parse query string (format: token=xxx)
        token = token.split('token=')[-1].split('&')[0] if 'token=' in token else None
        
        if not token:
            logger.warning("WebSocket connection attempt without token")
            await self.close(code=4001)  # Unauthorized
            return

        # Authenticate user
        try:
            user = await self.authenticate_token(token)
            if not user:
                logger.warning(f"WebSocket connection attempt with invalid token")
                await self.close(code=4001)  # Unauthorized
                return
            
            self.user = user
            self.user_id = user.id
            self.room_group_name = f'music_updates_{self.user_id}'
            
            # Join room group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )
            
            await self.accept()
            logger.info(f"WebSocket connected for user {self.user_id}")
            
        except Exception as e:
            logger.error(f"Error during WebSocket connection: {str(e)}", exc_info=True)
            await self.close(code=4002)  # Internal error

    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection.
        """
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected for user {getattr(self, 'user_id', 'unknown')}")

    async def receive(self, text_data):
        """
        Handle messages received from WebSocket.
        Currently not used, but can be extended for bidirectional communication.
        """
        try:
            data = json.loads(text_data)
            logger.debug(f"Received message from user {getattr(self, 'user_id', 'unknown')}: {data}")
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON received from WebSocket")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}", exc_info=True)

    async def music_generation_update(self, event):
        """
        Handle music generation update message from room group.
        Sends the update to WebSocket.
        """
        try:
            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'type': 'music_generation_update',
                'data': event['data']
            }))
            logger.debug(f"Sent music generation update to user {getattr(self, 'user_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Error sending music generation update: {str(e)}", exc_info=True)

    @database_sync_to_async
    def authenticate_token(self, token):
        """
        Authenticate JWT token and return user object.
        """
        try:
            # Validate token format
            UntypedToken(token)
            
            # Decode token to get user ID
            # Use SIGNING_KEY from SIMPLE_JWT settings if available, otherwise fall back to SECRET_KEY
            signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', settings.SECRET_KEY)
            decoded_data = jwt_decode(
                token,
                signing_key,
                algorithms=[settings.SIMPLE_JWT['ALGORITHM']]
            )
            
            # Get user ID from token
            user_id = decoded_data.get(settings.SIMPLE_JWT['USER_ID_CLAIM'])
            
            if not user_id:
                logger.warning("Token does not contain user_id claim")
                return None
            
            # Get user from database
            try:
                user = User.objects.get(id=user_id)
                return user
            except User.DoesNotExist:
                logger.warning(f"User with id {user_id} not found")
                return None
                
        except TokenError as e:
            logger.warning(f"Token error: {str(e)}")
            return None
        except InvalidToken as e:
            logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error authenticating token: {str(e)}", exc_info=True)
            return None

