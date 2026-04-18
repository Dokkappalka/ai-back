"""
WebSocket consumers for real-time updates.
"""
import json
import logging
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings

logger = logging.getLogger(__name__)

PROJECT_AI_MODEL = 'anthropic/claude-sonnet-4'

PROJECT_SYSTEM_PROMPT = """Ты — AI-продюсер музыкального проекта. Помогаешь пользователю создать музыку через Suno AI.

Веди диалог на русском языке. Задавай уточняющие вопросы о:
- Жанре и стиле музыки (примеры: lo-fi hip hop, dark ambient, pop punk, cinematic orchestral)
- Настроении и атмосфере (меланхолия, агрессия, эйфория, задумчивость и т.д.)
- Музыкальных референсах (исполнители, треки)
- Темпе (медленный/средний/быстрый)
- Вокале (мужской/женский/без вокала) — если вокальный трек, обязательно спроси об этом
- Тематике текстов (если есть вокал)
- Для альбома: как треки должны соотноситься между собой

Ты также помогаешь писать тексты песен. Если пользователь просит написать текст или слова для трека:
- Напиши ПОЛНЫЙ текст песни (куплет + припев + куплет + припев + бридж + финальный припев, или другую уместную структуру)
- Используй Suno-разметку: [Verse 1], [Chorus], [Bridge], [Outro] и т.д.
- Текст пиши на языке, который просит пользователь (или на английском по умолчанию)
- После написания текста сразу помести его в поле prompt соответствующего трека в JSON

Когда получишь достаточно информации для всех треков (и напишешь тексты если нужно) — заверши ответ JSON-блоком:

```json
{
  "ready_to_generate": true,
  "concept": "краткое описание концепции на русском",
  "tracks": [
    {
      "order": 1,
      "title": "Осенний Дождь",
      "style": "style tags in English for Suno, e.g. female vocals, lo-fi, melancholic piano",
      "prompt": "вокальный трек: ПОЛНЫЙ текст с [Verse 1], [Chorus] и т.д. | инструментал: детальное описание звука, настроения, инструментов, атмосферы на английском",
      "instrumental": false,
      "suno_model": "V4_5ALL",
      "negative_tags": "things to exclude in English"
    }
  ]
}
```

Строгие правила для поля title:
- Это НАЗВАНИЕ трека — короткое, образное, на РУССКОМ языке (можно на английском если стиль обязывает)
- Примеры хороших названий: "Ночной Город", "Broken Dreams", "Пустые Улицы", "Last Dance"
- НЕЛЬЗЯ: числа, идентификаторы, "Трек 1", "Track 1", шаблонный текст

Строгие правила для поля prompt:
- Вокальный трек: ОБЯЗАТЕЛЬНО полный текст песни с Suno-разметкой [Verse 1], [Chorus], [Bridge] и т.д.
  Если попросили написать текст — он идёт сюда. Не краткое описание, а сам текст.
  Пример: "[Verse 1]\nI walk these empty streets at night...\n[Chorus]\nFalling down..."
- Инструментальный трек: развёрнутое описание на английском — инструменты, темп, настроение, текстуры, атмосфера.
  Пример: "Slow melancholic piano melody with soft strings, distant rain sounds, late night jazz atmosphere, 70 BPM"

Строгие правила для поля style:
- Только английские теги через запятую: жанр, инструменты, темп, вокал (если есть)
- Для вокальных треков ОБЯЗАТЕЛЬНО укажи тип вокала: "female vocals", "male vocals", "deep female voice", "tenor" и т.д.

Важно:
- style, prompt и negative_tags — на английском
- title — на русском (или английском если стиль обязывает)
- Для альбома делай треки тематически связанными, но разными по звучанию
- JSON-блок добавляй В КОНЦЕ ответа, после любого текста к пользователю
- Не спрашивай лишнего — если пользователь уже дал достаточно информации, сразу выдай JSON"""


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


def _authenticate_token_sync(token):
    """Standalone sync JWT auth helper shared between consumers."""
    try:
        UntypedToken(token)
        signing_key = settings.SIMPLE_JWT.get('SIGNING_KEY', settings.SECRET_KEY)
        decoded_data = jwt_decode(
            token,
            signing_key,
            algorithms=[settings.SIMPLE_JWT['ALGORITHM']]
        )
        user_id = decoded_data.get(settings.SIMPLE_JWT['USER_ID_CLAIM'])
        if not user_id:
            return None
        return User.objects.get(id=user_id)
    except Exception:
        return None


class ProjectConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for AI-producer project chat.
    URL: ws/projects/<project_id>/chat/?token=<jwt>
    """

    async def connect(self):
        # Parse token
        qs = self.scope.get('query_string', b'').decode('utf-8')
        token = qs.split('token=')[-1].split('&')[0] if 'token=' in qs else None
        if not token:
            await self.close(code=4001)
            return

        user = await database_sync_to_async(_authenticate_token_sync)(token)
        if not user:
            await self.close(code=4001)
            return

        # Parse project_id from URL route kwargs
        self.project_id = self.scope['url_route']['kwargs'].get('project_id')
        if not self.project_id:
            await self.close(code=4003)
            return

        # Verify project belongs to this user
        project = await self._get_project(user, self.project_id)
        if not project:
            await self.close(code=4004)
            return

        self.user = user
        self.project = project
        self.room_group_name = f'project_{self.project_id}'

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        logger.info(f"ProjectConsumer connected: user={user.id}, project={self.project_id}")

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get('type', 'chat_message')

        if msg_type == 'chat_message':
            await self._handle_chat_message(data.get('message', ''))

    async def _handle_chat_message(self, user_message: str):
        if not user_message.strip():
            return

        # Save user message
        await self._save_message('user', user_message)

        # Build conversation history for OpenRouter
        history = await self._get_chat_history()
        project = await self._get_project_fresh()

        track_count = project.track_count
        project_type = 'альбом' if project.type == 'album' else 'сингл'

        system_prompt = PROJECT_SYSTEM_PROMPT + (
            f"\n\nПроект: {project_type}, {track_count} трека(ов)."
        )

        messages = [{'role': 'system', 'content': system_prompt}]
        messages += history

        full_response = ''
        try:
            from .services.openrouter_api import OpenRouterService
            service = OpenRouterService()
            async for chunk in service.chat_completion_stream_async(messages, model=PROJECT_AI_MODEL, temperature=0.7, max_tokens=4096):
                if chunk['type'] == 'chunk':
                    full_response += chunk['content']
                    await self.send(json.dumps({
                        'type': 'chat_chunk',
                        'content': chunk['content'],
                    }))
                elif chunk['type'] == 'done':
                    break
                elif chunk['type'] == 'error':
                    await self.send(json.dumps({'type': 'error', 'message': chunk.get('message', 'AI error')}))
                    return
        except Exception as e:
            logger.error(f"OpenRouter stream error in ProjectConsumer: {e}", exc_info=True)
            await self.send(json.dumps({'type': 'error', 'message': 'Ошибка AI-сервиса'}))
            return

        # Try to extract JSON tracks data
        track_data = self._extract_json(full_response)

        # Strip JSON block from the visible message before saving / displaying
        visible_response = self._strip_json_block(full_response).strip()

        # Save assistant message (without raw JSON)
        await self._save_message('assistant', visible_response)

        if track_data and track_data.get('ready_to_generate'):
            updated_tracks = await self._apply_track_data(track_data)
            await self.send(json.dumps({
                'type': 'tracks_update',
                'ready_to_generate': True,
                'concept': track_data.get('concept', ''),
                'tracks': updated_tracks,
            }))

        await self.send(json.dumps({'type': 'chat_done', 'visible_response': visible_response}))

    def _extract_json(self, text: str):
        """Extract first JSON object from markdown code block or raw text."""
        # Try markdown ```json ... ``` block
        match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        # Try raw JSON object
        match = re.search(r'\{[\s\S]*"ready_to_generate"[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    def _strip_json_block(self, text: str) -> str:
        """Remove the JSON block from text — cuts everything from the block start to end."""
        # Try ```json fence first
        idx = text.find('```json')
        if idx != -1:
            return text[:idx].strip()
        # Try raw JSON object with ready_to_generate (always at the end per prompt instructions)
        match = re.search(r'\{[^{}]*"ready_to_generate"', text)
        if match:
            return text[:match.start()].strip()
        return text

    @database_sync_to_async
    def _get_project(self, user, project_id):
        from .models import Project
        try:
            return Project.objects.get(id=project_id, user=user)
        except Project.DoesNotExist:
            return None

    @database_sync_to_async
    def _get_project_fresh(self):
        from .models import Project
        return Project.objects.get(id=self.project_id)

    @database_sync_to_async
    def _save_message(self, role: str, content: str):
        from .models import ProjectChatMessage
        ProjectChatMessage.objects.create(
            project_id=self.project_id,
            role=role,
            content=content,
        )

    @database_sync_to_async
    def _get_chat_history(self):
        from .models import ProjectChatMessage
        msgs = ProjectChatMessage.objects.filter(project_id=self.project_id).order_by('created_at')
        return [{'role': m.role, 'content': m.content} for m in msgs]

    @database_sync_to_async
    def _apply_track_data(self, track_data: dict):
        """Update ProjectTrack rows with AI-generated data, return serializable list."""
        from .models import Project, ProjectTrack
        project = Project.objects.get(id=self.project_id)

        # Update concept
        concept = track_data.get('concept', '')
        if concept:
            project.concept = concept
            project.save(update_fields=['concept'])

        result = []
        for t in track_data.get('tracks', []):
            order = t.get('order', 1)
            track, _ = ProjectTrack.objects.get_or_create(
                project=project,
                order=order,
            )
            if t.get('title'):
                track.title = t['title']
            if t.get('style'):
                track.suno_style = t['style']
            if t.get('prompt'):
                track.suno_prompt = t['prompt']
            if 'instrumental' in t:
                track.suno_instrumental = bool(t['instrumental'])
            if t.get('suno_model'):
                track.suno_model = t['suno_model']
            if t.get('negative_tags'):
                track.suno_negative_tags = t['negative_tags']
            track.save()
            result.append({
                'id': track.id,
                'order': track.order,
                'title': track.title,
                'suno_style': track.suno_style,
                'suno_prompt': track.suno_prompt,
                'suno_instrumental': track.suno_instrumental,
                'suno_model': track.suno_model,
                'suno_negative_tags': track.suno_negative_tags,
                'status': track.status,
            })
        return result

    async def project_track_update(self, event):
        """Receive track update from channel layer and forward to WebSocket."""
        await self.send(json.dumps({
            'type': 'track_status_update',
            'data': event['data'],
        }))

