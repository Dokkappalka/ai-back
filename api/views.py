import base64
import json
import mimetypes

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.conf import settings
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from .models import (
    ImageGeneration, VideoGeneration, MusicGeneration,
    Conversation, ChatMessage, ChatMessageAttachment,
)
from .serializers import (
    ImageGenerationSerializer,
    VideoGenerationSerializer,
    MusicGenerationSerializer,
    ConversationSerializer,
    ChatMessageSerializer,
    ChatMessageAttachmentSerializer,
    SendMessageSerializer,
)
from .services.suno_api import SunoAPIService

logger = logging.getLogger(__name__)

# Maximum file size for chat attachments (20 MB)
MAX_ATTACHMENT_SIZE = 20 * 1024 * 1024

# Allowed MIME types for chat attachments
ALLOWED_IMAGE_TYPES = {'image/png', 'image/jpeg', 'image/gif', 'image/webp', 'image/svg+xml'}
ALLOWED_TEXT_TYPES = {'text/plain', 'text/csv', 'text/html', 'text/markdown',
                      'application/json', 'application/xml', 'text/xml'}
ALLOWED_DOC_TYPES = {'application/pdf'}
ALLOWED_MIME_TYPES = ALLOWED_IMAGE_TYPES | ALLOWED_TEXT_TYPES | ALLOWED_DOC_TYPES


class ImageGenerationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for image generation endpoints.
    
    Endpoints:
    - GET /api/image/ - List all image generation requests
    - POST /api/image/ - Create a new image generation request
    - GET /api/image/{id}/ - Get a specific image generation request
    """
    serializer_class = ImageGenerationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return ImageGeneration.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='pending')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class VideoGenerationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for video generation endpoints.
    
    Endpoints:
    - GET /api/video/ - List all video generation requests
    - POST /api/video/ - Create a new video generation request
    - GET /api/video/{id}/ - Get a specific video generation request
    """
    serializer_class = VideoGenerationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return VideoGeneration.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='pending')

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MusicGenerationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for music generation endpoints using Suno API.
    
    Endpoints:
    - GET /api/music/ - List music generation requests (filtered by user if authenticated)
    - POST /api/music/ - Create a new music generation request
    - GET /api/music/{id}/ - Get a specific music generation request
    - GET /api/music/{id}/status/ - Check generation status
    """
    serializer_class = MusicGenerationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MusicGeneration.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if instance.task_id and instance.status == 'processing':
            try:
                suno_service = SunoAPIService()
                api_response = suno_service.get_generation_details(instance.task_id)
                parsed_data = suno_service.parse_generation_response(api_response)
                
                instance.status = parsed_data['status']
                
                if parsed_data.get('song_1_url'):
                    instance.song_1_url = parsed_data['song_1_url']
                if parsed_data.get('song_1_stream_url'):
                    instance.song_1_stream_url = parsed_data['song_1_stream_url']
                if parsed_data.get('song_1_id'):
                    instance.song_1_id = parsed_data['song_1_id']
                if parsed_data.get('song_1_image_url'):
                    instance.song_1_image_url = parsed_data['song_1_image_url']
                if parsed_data.get('song_1_duration') is not None:
                    instance.song_1_duration = parsed_data['song_1_duration']
                if parsed_data.get('song_1_tags'):
                    instance.song_1_tags = parsed_data['song_1_tags']
                if parsed_data.get('song_1_model_name'):
                    instance.song_1_model_name = parsed_data['song_1_model_name']
                
                if parsed_data.get('song_2_url'):
                    instance.song_2_url = parsed_data['song_2_url']
                if parsed_data.get('song_2_stream_url'):
                    instance.song_2_stream_url = parsed_data['song_2_stream_url']
                if parsed_data.get('song_2_id'):
                    instance.song_2_id = parsed_data['song_2_id']
                if parsed_data.get('song_2_image_url'):
                    instance.song_2_image_url = parsed_data['song_2_image_url']
                if parsed_data.get('song_2_duration') is not None:
                    instance.song_2_duration = parsed_data['song_2_duration']
                if parsed_data.get('song_2_tags'):
                    instance.song_2_tags = parsed_data['song_2_tags']
                if parsed_data.get('song_2_model_name'):
                    instance.song_2_model_name = parsed_data['song_2_model_name']
                
                if parsed_data.get('error_message'):
                    instance.error_message = parsed_data['error_message']
                if parsed_data.get('error_code'):
                    instance.error_code = parsed_data['error_code']
                
                instance.save()
                    
            except Exception as e:
                logger.error(f"Failed to auto-update status from Suno API for task {instance.task_id}: {str(e)}")
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, status='pending')
        
        instance = serializer.instance
        
        try:
            suno_service = SunoAPIService()
            callback_url = f"{settings.BASE_URL}/api/music/callback/"
            
            suno_params = {
                'custom_mode': instance.custom_mode,
                'instrumental': instance.instrumental,
                'model': instance.model,
            }
            
            if instance.prompt:
                suno_params['prompt'] = instance.prompt
            if instance.style:
                suno_params['style'] = instance.style
            if instance.title:
                suno_params['title'] = instance.title
            if instance.persona_id:
                suno_params['persona_id'] = instance.persona_id
            if instance.negative_tags:
                suno_params['negative_tags'] = instance.negative_tags
            if instance.vocal_gender:
                suno_params['vocal_gender'] = instance.vocal_gender
            if instance.style_weight is not None:
                suno_params['style_weight'] = float(instance.style_weight)
            if instance.weirdness_constraint is not None:
                suno_params['weirdness_constraint'] = float(instance.weirdness_constraint)
            if instance.audio_weight is not None:
                suno_params['audio_weight'] = float(instance.audio_weight)
            suno_params['callback_url'] = callback_url
            
            response = suno_service.generate_music(**suno_params)
            
            if response.get('code') == 200 and response.get('data', {}).get('taskId'):
                instance.task_id = response['data']['taskId']
                instance.status = 'processing'
                instance.save()
            else:
                instance.status = 'failed'
                instance.error_message = response.get('msg', 'Unknown error from Suno API')
                instance.error_code = response.get('code', 500)
                instance.save()
                
        except ValueError as e:
            instance.status = 'failed'
            instance.error_message = f"Configuration error: {str(e)}"
            instance.save()
        except Exception as e:
            instance.status = 'failed'
            instance.error_message = f"Failed to call Suno API: {str(e)}"
            instance.save()

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        instance = self.get_object()
        
        if instance.user != request.user:
            return Response(
                {'error': 'You do not have permission to view this generation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if instance.task_id and instance.status == 'processing':
            try:
                suno_service = SunoAPIService()
                api_response = suno_service.get_generation_details(instance.task_id)
                parsed_data = suno_service.parse_generation_response(api_response)
                
                instance.status = parsed_data['status']
                
                if parsed_data.get('song_1_url'):
                    instance.song_1_url = parsed_data['song_1_url']
                if parsed_data.get('song_1_stream_url'):
                    instance.song_1_stream_url = parsed_data['song_1_stream_url']
                if parsed_data.get('song_1_id'):
                    instance.song_1_id = parsed_data['song_1_id']
                if parsed_data.get('song_1_image_url'):
                    instance.song_1_image_url = parsed_data['song_1_image_url']
                if parsed_data.get('song_1_duration') is not None:
                    instance.song_1_duration = parsed_data['song_1_duration']
                if parsed_data.get('song_1_tags'):
                    instance.song_1_tags = parsed_data['song_1_tags']
                if parsed_data.get('song_1_model_name'):
                    instance.song_1_model_name = parsed_data['song_1_model_name']
                
                if parsed_data.get('song_2_url'):
                    instance.song_2_url = parsed_data['song_2_url']
                if parsed_data.get('song_2_stream_url'):
                    instance.song_2_stream_url = parsed_data['song_2_stream_url']
                if parsed_data.get('song_2_id'):
                    instance.song_2_id = parsed_data['song_2_id']
                if parsed_data.get('song_2_image_url'):
                    instance.song_2_image_url = parsed_data['song_2_image_url']
                if parsed_data.get('song_2_duration') is not None:
                    instance.song_2_duration = parsed_data['song_2_duration']
                if parsed_data.get('song_2_tags'):
                    instance.song_2_tags = parsed_data['song_2_tags']
                if parsed_data.get('song_2_model_name'):
                    instance.song_2_model_name = parsed_data['song_2_model_name']
                
                if parsed_data.get('error_message'):
                    instance.error_message = parsed_data['error_message']
                if parsed_data.get('error_code'):
                    instance.error_code = parsed_data['error_code']
                
                instance.save()
                    
            except Exception as e:
                logger.error(f"Failed to fetch status from Suno API for task {instance.task_id}: {str(e)}")
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MusicGenerationCallbackView(APIView):
    """
    Callback endpoint for Suno API to notify about generation status updates.
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            logger.info(
                "Suno callback received: method=%s path=%s query_params=%s",
                request.method,
                request.get_full_path(),
                dict(request.query_params),
            )

            safe_headers = {}
            for key, value in request.META.items():
                if not key.startswith("HTTP_"):
                    continue
                header_name = key[5:].replace("_", "-").title()
                if header_name.lower() in {"authorization", "cookie"}:
                    safe_headers[header_name] = "***redacted***"
                else:
                    safe_headers[header_name] = value

            logger.debug("Suno callback headers: %s", safe_headers)

            try:
                raw_body = request.body.decode("utf-8", errors="replace")
            except Exception:
                raw_body = "<unreadable body>"

            if len(raw_body) > 4000:
                raw_body_log = raw_body[:4000] + "... [truncated]"
            else:
                raw_body_log = raw_body

            logger.debug("Suno callback raw body: %s", raw_body_log)
            logger.debug("Suno callback parsed data: %s", request.data)
        except Exception as log_exc:
            logger.error("Failed to log Suno callback request: %s", str(log_exc))

        try:
            task_id = (
                request.data.get('taskId') or 
                request.data.get('task_id') or
                request.data.get('data', {}).get('task_id') or
                request.data.get('data', {}).get('taskId')
            )
            
            if not task_id:
                logger.warning(f"Callback received without taskId. Received data: {request.data}")
                return Response(
                    {'error': 'taskId is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                instance = MusicGeneration.objects.get(task_id=task_id)
            except MusicGeneration.DoesNotExist:
                logger.warning(f"Callback received for unknown task_id: {task_id}")
                return Response(
                    {'error': 'Task not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            suno_service = SunoAPIService()
            parsed_data = suno_service.parse_callback_response(request.data)
            
            logger.info(f"Parsed callback data for task {task_id}: status={parsed_data.get('status')}, "
                       f"song_1_url={parsed_data.get('song_1_url')}, song_1_stream_url={parsed_data.get('song_1_stream_url')}, "
                       f"song_1_image_url={parsed_data.get('song_1_image_url')}, song_1_duration={parsed_data.get('song_1_duration')}, "
                       f"song_1_tags={parsed_data.get('song_1_tags')}, song_1_model_name={parsed_data.get('song_1_model_name')}")
            
            instance.status = parsed_data['status']
            
            if parsed_data.get('song_1_url'):
                instance.song_1_url = parsed_data['song_1_url']
            if parsed_data.get('song_1_stream_url'):
                instance.song_1_stream_url = parsed_data['song_1_stream_url']
            if parsed_data.get('song_1_id'):
                instance.song_1_id = parsed_data['song_1_id']
            if parsed_data.get('song_1_image_url'):
                instance.song_1_image_url = parsed_data['song_1_image_url']
            if parsed_data.get('song_1_duration') is not None:
                instance.song_1_duration = parsed_data['song_1_duration']
            if parsed_data.get('song_1_tags'):
                instance.song_1_tags = parsed_data['song_1_tags']
            if parsed_data.get('song_1_model_name'):
                instance.song_1_model_name = parsed_data['song_1_model_name']
            
            if parsed_data.get('song_2_url'):
                instance.song_2_url = parsed_data['song_2_url']
            if parsed_data.get('song_2_stream_url'):
                instance.song_2_stream_url = parsed_data['song_2_stream_url']
            if parsed_data.get('song_2_id'):
                instance.song_2_id = parsed_data['song_2_id']
            if parsed_data.get('song_2_image_url'):
                instance.song_2_image_url = parsed_data['song_2_image_url']
            if parsed_data.get('song_2_duration') is not None:
                instance.song_2_duration = parsed_data['song_2_duration']
            if parsed_data.get('song_2_tags'):
                instance.song_2_tags = parsed_data['song_2_tags']
            if parsed_data.get('song_2_model_name'):
                instance.song_2_model_name = parsed_data['song_2_model_name']
            
            if parsed_data.get('error_message'):
                instance.error_message = parsed_data['error_message']
            if parsed_data.get('error_code'):
                instance.error_code = parsed_data['error_code']
            
            instance.save()
            
            logger.info(f"Successfully processed callback for task {task_id}, status: {instance.status}")
            
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    serializer = MusicGenerationSerializer(instance)
                    group_name = f'music_updates_{instance.user.id}'
                    async_to_sync(channel_layer.group_send)(
                        group_name,
                        {
                            'type': 'music_generation_update',
                            'data': serializer.data
                        }
                    )
                    logger.info(f"Sent WebSocket update to group {group_name} for task {task_id}")
                else:
                    logger.warning("Channel layer not available, skipping WebSocket update")
            except Exception as ws_error:
                logger.error(f"Error sending WebSocket update: {str(ws_error)}", exc_info=True)
            
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing callback: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =====================
# Chat with OpenRouter
# =====================

def _classify_file_type(mime_type):
    """Classify a MIME type into our attachment type categories."""
    if mime_type in ALLOWED_IMAGE_TYPES:
        return 'image'
    elif mime_type in ALLOWED_TEXT_TYPES:
        return 'text'
    elif mime_type in ALLOWED_DOC_TYPES:
        return 'pdf'
    return 'other'


def _build_api_message_content(msg):
    """
    Build the OpenRouter API message content for a ChatMessage.
    If the message has image attachments, returns a list (multimodal content).
    Otherwise returns a plain string.
    """
    attachments = msg.attachments.all()
    if not attachments.exists():
        return msg.content

    # Build multimodal content array (OpenAI vision format)
    content_parts = []

    # Add text part first
    if msg.content:
        content_parts.append({
            'type': 'text',
            'text': msg.content,
        })
    else:
        # Fallback text when there are attachments but no text content
        content_parts.append({
            'type': 'text',
            'text': 'Attached file(s)',
        })

    for attachment in attachments:
        if attachment.is_image:
            if attachment.mime_type == 'image/svg+xml':
                # Pass SVG source code as text since vision models might not natively support SVG
                try:
                    file_data = attachment.file.read()
                    attachment.file.seek(0)
                    text_content = file_data.decode('utf-8', errors='replace')
                    if len(text_content) > 50000:
                        text_content = text_content[:50000] + "\n...[SVG TRUNCATED DUE TO SIZE LIMIT]..."
                    content_parts.append({
                        'type': 'text',
                        'text': f"\n--- SVG Image: {attachment.original_filename} ---\n{text_content}\n--- End of SVG ---\n",
                    })
                except Exception as e:
                    logger.warning(f"Failed to read SVG attachment {attachment.id}: {e}")
            else:
                # Convert image to base64 data URL for vision models
                try:
                    file_data = attachment.file.read()
                    attachment.file.seek(0)  # Reset file pointer
                    b64_data = base64.b64encode(file_data).decode('utf-8')
                    data_url = f"data:{attachment.mime_type};base64,{b64_data}"
                    content_parts.append({
                        'type': 'image_url',
                        'image_url': {
                            'url': data_url,
                        },
                    })
                except Exception as e:
                    logger.warning(f"Failed to read image attachment {attachment.id}: {e}")
        elif attachment.is_text:
            # Read text file content and include as text
            try:
                file_data = attachment.file.read()
                attachment.file.seek(0)
                text_content = file_data.decode('utf-8', errors='replace')
                if len(text_content) > 100000:
                    text_content = text_content[:100000] + "\n...[FILE TRUNCATED DUE TO SIZE LIMIT]..."
                content_parts.append({
                    'type': 'text',
                    'text': f"\n--- File: {attachment.original_filename} ---\n{text_content}\n--- End of file ---\n",
                })
            except Exception as e:
                logger.warning(f"Failed to read text attachment {attachment.id}: {e}")
        # For PDFs and other files, we include them as text description
        # (most LLMs can't process raw binary; PDF text extraction would need extra libs)
        else:
            content_parts.append({
                'type': 'text',
                'text': f"[Attached file: {attachment.original_filename} ({attachment.mime_type}, {attachment.file_size} bytes)]",
            })

    return content_parts if content_parts else msg.content


def _save_attachments(user_message, files):
    """
    Save uploaded files as ChatMessageAttachment objects.
    Returns list of created attachments.
    """
    attachments = []
    for f in files:
        mime_type = f.content_type or mimetypes.guess_type(f.name)[0] or 'application/octet-stream'
        file_type = _classify_file_type(mime_type)

        attachment = ChatMessageAttachment.objects.create(
            message=user_message,
            file=f,
            original_filename=f.name,
            file_type=file_type,
            mime_type=mime_type,
            file_size=f.size,
        )
        attachments.append(attachment)
    return attachments


def _get_modalities(model_id):
    """
    Determine the modalities parameter for an OpenRouter API request.
    Returns ['image', 'text'] for models that support image output, None otherwise.
    """
    from .services.openrouter_api import OpenRouterService
    metadata = OpenRouterService._fetch_all_models_metadata()
    meta = metadata.get(model_id, {})
    modality = meta.get('modality', '')
    # modality looks like 'text+image->text+image' or 'text->text'
    if '->' in modality:
        output_part = modality.split('->')[1]
        if 'image' in output_part:
            return ['image', 'text']
    return None


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing chat conversations.

    Endpoints:
    - GET    /api/chat/conversations/                           - List conversations
    - POST   /api/chat/conversations/                           - Create a conversation
    - GET    /api/chat/conversations/{id}/                       - Get conversation details
    - PATCH  /api/chat/conversations/{id}/                       - Update conversation (title, model, etc.)
    - DELETE /api/chat/conversations/{id}/                       - Delete conversation
    - GET    /api/chat/conversations/{id}/messages/              - Get messages in a conversation
    - POST   /api/chat/conversations/{id}/send_message/          - Send message & get AI response (non-streaming, legacy)
    - POST   /api/chat/conversations/{id}/send_message_stream/   - Send message & get AI response via SSE streaming
    - POST   /api/chat/conversations/{id}/archive/               - Archive conversation
    - POST   /api/chat/conversations/{id}/unarchive/             - Unarchive conversation
    """
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_queryset(self):
        """
        Filter conversations by current user.
        Optionally filter by is_archived query param.
        """
        queryset = Conversation.objects.filter(user=self.request.user)

        # Filter by is_archived if specified
        is_archived = self.request.query_params.get('is_archived')
        if is_archived is not None:
            queryset = queryset.filter(is_archived=is_archived.lower() == 'true')

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get all messages in a conversation, including attachments.
        """
        conversation = self.get_object()
        messages = ChatMessage.objects.filter(
            conversation=conversation
        ).prefetch_related('attachments')
        serializer = ChatMessageSerializer(messages, many=True, context={'request': request})
        return Response(serializer.data)

    def _validate_and_extract_request(self, request):
        """
        Validate the send_message request and extract content + files.
        Returns (content, files) tuple.
        Raises ValidationError on invalid input.
        """
        # Handle both JSON and multipart/form-data
        content = request.data.get('content', '')
        files = request.FILES.getlist('files')

        if not content and not files:
            from rest_framework.exceptions import ValidationError
            raise ValidationError({'content': 'Message content is required (or attach files).'})

        if not content:
            content = ''

        # Validate files
        for f in files:
            if f.size > MAX_ATTACHMENT_SIZE:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'files': f'File "{f.name}" exceeds maximum size of {MAX_ATTACHMENT_SIZE // (1024*1024)} MB.'
                })
            mime_type = f.content_type or mimetypes.guess_type(f.name)[0] or 'application/octet-stream'
            if mime_type not in ALLOWED_MIME_TYPES:
                from rest_framework.exceptions import ValidationError
                raise ValidationError({
                    'files': f'File type "{mime_type}" is not supported. '
                             f'Supported types: images (PNG, JPEG, GIF, WebP, SVG), '
                             f'text files (TXT, CSV, HTML, MD, JSON, XML), PDF.'
                })

        return content, files

    def _build_api_messages(self, conversation):
        """
        Build the full messages list for the OpenRouter API,
        including system prompt and conversation history with attachments.
        """
        api_messages = []

        # Add system prompt if set
        if conversation.system_prompt:
            api_messages.append({
                'role': 'system',
                'content': conversation.system_prompt,
            })

        # Add conversation history (with multimodal content for messages with attachments)
        history = ChatMessage.objects.filter(
            conversation=conversation
        ).prefetch_related('attachments').order_by('created_at')

        for msg in history:
            api_messages.append({
                'role': msg.role,
                'content': _build_api_message_content(msg),
            })

        return api_messages

    @action(detail=True, methods=['post'], url_path='send_message')
    def send_message(self, request, pk=None):
        """
        Send a message to a conversation and get an AI response (non-streaming).
        Kept for backward compatibility. Supports file attachments via multipart/form-data.

        Request body (JSON):
        {
            "content": "Hello, how are you?"
        }

        Request body (multipart/form-data):
        - content: "Hello, what's in this image?"
        - files: [file1, file2, ...]

        Response:
        {
            "user_message": { ... },
            "assistant_message": { ... }
        }
        """
        conversation = self.get_object()

        # Validate request
        content, files = self._validate_and_extract_request(request)

        # Save user message
        user_message = ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content=content,
            user=request.user,
        )

        # Save attachments if any
        if files:
            _save_attachments(user_message, files)

        # Build messages list for OpenRouter API
        api_messages = self._build_api_messages(conversation)

        # Call OpenRouter API
        try:
            from .services.openrouter_api import OpenRouterService

            service = OpenRouterService()
            modalities = _get_modalities(conversation.model)
            result = service.chat_completion(
                messages=api_messages,
                model=conversation.model,
                temperature=conversation.temperature,
                max_tokens=conversation.max_tokens,
                modalities=modalities,
            )

            # Save assistant message
            assistant_message = ChatMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content=result['content'],
                model=result['model'],
                tokens_used=result['usage'].get('total_tokens'),
                user=request.user,
            )

            # Update conversation's updated_at
            conversation.save()  # triggers auto_now on updated_at

            # Auto-generate title from first user message if still default
            if conversation.title == 'New Chat':
                conversation.title = content[:50] + ('...' if len(content) > 50 else '')
                conversation.save()

            return Response({
                'user_message': ChatMessageSerializer(user_message, context={'request': request}).data,
                'assistant_message': ChatMessageSerializer(assistant_message, context={'request': request}).data,
            }, status=status.HTTP_201_CREATED)

        except ValueError as e:
            user_message.delete()
            return Response(
                {'error': f'Configuration error: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.error(f"OpenRouter API error: {str(e)}", exc_info=True)
            assistant_message = ChatMessage.objects.create(
                conversation=conversation,
                role='assistant',
                content='Sorry, an error occurred while generating a response. Please try again.',
                user=request.user,
            )
            return Response({
                'user_message': ChatMessageSerializer(user_message, context={'request': request}).data,
                'assistant_message': ChatMessageSerializer(assistant_message, context={'request': request}).data,
                'error': str(e),
            }, status=status.HTTP_502_BAD_GATEWAY)

    @action(detail=True, methods=['post'], url_path='send_message_stream')
    def send_message_stream(self, request, pk=None):
        """
        Send a message and get an AI response via SSE.
        View is sync (for DRF), but returns StreamingHttpResponse with an
        async generator that Daphne/ASGI iterates for true streaming.
        """
        conversation = self.get_object()

        # Validate request
        try:
            content, files = self._validate_and_extract_request(request)
        except Exception as e:
            err_msg = str(e)
            async def error_stream():
                yield f"event: error\ndata: {json.dumps({'error': err_msg})}\n\n"
            return StreamingHttpResponse(
                error_stream(),
                content_type='text/event-stream',
                status=400,
            )

        # All sync DB work upfront — before entering the async generator
        user_message = ChatMessage.objects.create(
            conversation=conversation,
            role='user',
            content=content,
            user=request.user,
        )

        if files:
            _save_attachments(user_message, files)

        user_message_data = ChatMessageSerializer(user_message, context={'request': request}).data
        api_messages = self._build_api_messages(conversation)

        if conversation.title == 'New Chat':
            conversation.title = content[:50] + ('...' if len(content) > 50 else '')
            conversation.save()

        modalities = _get_modalities(conversation.model)

        # Capture values needed inside the async generator
        conv_model = conversation.model
        conv_temp = conversation.temperature
        conv_max_tokens = conversation.max_tokens
        conv_id = conversation.id
        user_id = request.user.id

        async def event_stream():
            """Async generator — Daphne/ASGI iterates this for true streaming."""
            from asgiref.sync import sync_to_async

            yield f"event: user_message\ndata: {json.dumps(user_message_data, ensure_ascii=False)}\n\n"

            full_content = ''
            used_model = conv_model
            usage = {}
            finish_reason = 'stop'
            had_error = False

            try:
                from .services.openrouter_api import OpenRouterService
                service = OpenRouterService()

                async for chunk in service.chat_completion_stream_async(
                    messages=api_messages,
                    model=conv_model,
                    temperature=conv_temp,
                    max_tokens=conv_max_tokens,
                    modalities=modalities,
                ):
                    chunk_type = chunk.get('type')

                    if chunk_type == 'chunk':
                        delta = chunk.get('content', '')
                        full_content += delta
                        yield f"event: chunk\ndata: {json.dumps({'content': delta}, ensure_ascii=False)}\n\n"

                    elif chunk_type == 'done':
                        used_model = chunk.get('model', conv_model)
                        usage = chunk.get('usage', {})
                        finish_reason = chunk.get('finish_reason', 'stop')

                    elif chunk_type == 'error':
                        had_error = True
                        error_msg = chunk.get('content', 'Unknown streaming error')
                        logger.error(f"OpenRouter streaming error: {error_msg}")

                        def _create_error_msg():
                            from django.contrib.auth.models import User
                            user = User.objects.get(id=user_id)
                            conv = Conversation.objects.get(id=conv_id)
                            msg = ChatMessage.objects.create(
                                conversation=conv,
                                role='assistant',
                                content='Sorry, an error occurred while generating a response.',
                                user=user,
                            )
                            return ChatMessageSerializer(msg).data

                        assistant_data = await sync_to_async(_create_error_msg)()
                        yield f"event: error\ndata: {json.dumps({'error': error_msg, 'assistant_message': assistant_data}, ensure_ascii=False)}\n\n"
                        return

            except ValueError as e:
                await sync_to_async(ChatMessage.objects.filter(id=user_message.id).delete)()
                yield f"event: error\ndata: {json.dumps({'error': f'Configuration error: {str(e)}'})}\n\n"
                return
            except Exception as e:
                logger.error(f"OpenRouter streaming error: {str(e)}", exc_info=True)

                def _create_error_msg_exc():
                    from django.contrib.auth.models import User
                    user = User.objects.get(id=user_id)
                    conv = Conversation.objects.get(id=conv_id)
                    msg = ChatMessage.objects.create(
                        conversation=conv,
                        role='assistant',
                        content='Sorry, an error occurred while generating a response.',
                        user=user,
                    )
                    return ChatMessageSerializer(msg).data

                assistant_data = await sync_to_async(_create_error_msg_exc)()
                yield f"event: error\ndata: {json.dumps({'error': str(e), 'assistant_message': assistant_data}, ensure_ascii=False)}\n\n"
                return

            if not had_error:
                def _save_assistant():
                    from django.contrib.auth.models import User
                    user = User.objects.get(id=user_id)
                    conv = Conversation.objects.get(id=conv_id)
                    msg = ChatMessage.objects.create(
                        conversation=conv,
                        role='assistant',
                        content=full_content or '',
                        model=used_model,
                        tokens_used=usage.get('total_tokens'),
                        user=user,
                    )
                    conv.save()
                    return ChatMessageSerializer(msg).data

                assistant_data = await sync_to_async(_save_assistant)()

                yield f"event: done\ndata: {json.dumps({'assistant_message': assistant_data, 'model': used_model, 'usage': usage, 'finish_reason': finish_reason}, ensure_ascii=False)}\n\n"

        response = StreamingHttpResponse(
            event_stream(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a conversation."""
        conversation = self.get_object()
        conversation.is_archived = True
        conversation.save()
        return Response(ConversationSerializer(conversation).data)

    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """Unarchive a conversation."""
        conversation = self.get_object()
        conversation.is_archived = False
        conversation.save()
        return Response(ConversationSerializer(conversation).data)


class AvailableModelsView(APIView):
    """
    GET /api/chat/models/ - List available AI models with capabilities info.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        from .services.openrouter_api import OpenRouterService
        models = OpenRouterService.get_available_models()
        return Response(models)
