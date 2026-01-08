from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging
from .models import ImageGeneration, VideoGeneration, MusicGeneration, ChatMessage
from .serializers import (
    ImageGenerationSerializer,
    VideoGenerationSerializer,
    MusicGenerationSerializer,
    ChatMessageSerializer,
)
from .services.suno_api import SunoAPIService

logger = logging.getLogger(__name__)


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
        """
        Filter queryset by current user.
        Users can only see their own generation requests.
        """
        return ImageGeneration.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically assign the current user to the generation request.
        """
        serializer.save(user=self.request.user, status='pending')

    def create(self, request, *args, **kwargs):
        """
        Create a new image generation request.
        Currently returns a placeholder response.
        TODO: Integrate with actual image generation model/API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the generation request (user is set in perform_create)
        self.perform_create(serializer)
        instance = serializer.instance
        
        # TODO: Trigger actual image generation here
        # For now, just return the created instance
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


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
        """
        Filter queryset by current user.
        Users can only see their own generation requests.
        """
        return VideoGeneration.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically assign the current user to the generation request.
        """
        serializer.save(user=self.request.user, status='pending')

    def create(self, request, *args, **kwargs):
        """
        Create a new video generation request.
        Currently returns a placeholder response.
        TODO: Integrate with actual video generation model/API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the generation request (user is set in perform_create)
        self.perform_create(serializer)
        instance = serializer.instance
        
        # TODO: Trigger actual video generation here
        # For now, just return the created instance
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


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
        """
        Filter queryset by current user.
        Users can only see their own generation requests.
        """
        return MusicGeneration.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve a specific music generation request.
        Automatically updates status from Suno API if status is 'processing'.
        """
        instance = self.get_object()
        
        # Automatically update status if still processing
        if instance.task_id and instance.status == 'processing':
            try:
                suno_service = SunoAPIService()
                api_response = suno_service.get_generation_details(instance.task_id)
                
                # Parse response and update instance
                parsed_data = suno_service.parse_generation_response(api_response)
                
                # Update instance fields
                instance.status = parsed_data['status']
                
                # Update song 1 data
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
                
                # Update song 2 data
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
                # If API call fails, continue with current status from database
                # Log the error but don't fail the request
                logger.error(f"Failed to auto-update status from Suno API for task {instance.task_id}: {str(e)}")
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        """
        Create a new music generation request and trigger Suno API.
        Automatically assign the current user.
        """
        serializer.save(user=self.request.user, status='pending')
        
        instance = serializer.instance
        
        # Call Suno API
        try:
            suno_service = SunoAPIService()
            
            # Prepare callback URL (required by Suno API)
            callback_url = f"{settings.BASE_URL}/api/music/callback/"
            
            # Prepare parameters for Suno API
            suno_params = {
                'custom_mode': instance.custom_mode,
                'instrumental': instance.instrumental,
                'model': instance.model,
            }
            
            # Add optional parameters (using Python naming, service will convert to API naming)
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
            # Always include callback_url as it's required by Suno API
            suno_params['callback_url'] = callback_url
            
            # Call Suno API
            response = suno_service.generate_music(**suno_params)
            
            # Update instance with task_id
            if response.get('code') == 200 and response.get('data', {}).get('taskId'):
                instance.task_id = response['data']['taskId']
                instance.status = 'processing'
                instance.save()
            else:
                # Handle API error
                instance.status = 'failed'
                instance.error_message = response.get('msg', 'Unknown error from Suno API')
                instance.error_code = response.get('code', 500)
                instance.save()
                
        except ValueError as e:
            # API key not configured
            instance.status = 'failed'
            instance.error_message = f"Configuration error: {str(e)}"
            instance.save()
        except Exception as e:
            # Other errors
            instance.status = 'failed'
            instance.error_message = f"Failed to call Suno API: {str(e)}"
            instance.save()

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Check the status of a music generation request.
        Fetches latest status from Suno API and updates the database.
        """
        instance = self.get_object()
        
        # Check if user has permission to view this instance
        # (get_queryset already filters by user, but double-check for safety)
        if instance.user != request.user:
            return Response(
                {'error': 'You do not have permission to view this generation.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # If task_id exists, try to fetch latest status from Suno API
        if instance.task_id and instance.status == 'processing':
            try:
                suno_service = SunoAPIService()
                api_response = suno_service.get_generation_details(instance.task_id)
                
                # Parse response and update instance
                parsed_data = suno_service.parse_generation_response(api_response)
                
                # Update instance fields
                instance.status = parsed_data['status']
                
                # Update song 1 data
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
                
                # Update song 2 data
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
                # If API call fails, return current status from database
                # Log the error but don't fail the request
                logger.error(f"Failed to fetch status from Suno API for task {instance.task_id}: {str(e)}")
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MusicGenerationCallbackView(APIView):
    """
    Callback endpoint for Suno API to notify about generation status updates.
    This endpoint should be publicly accessible (no authentication required)
    as Suno API will call it directly.
    """
    permission_classes = [AllowAny]
    authentication_classes = []  # Disable authentication completely
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        """
        Override dispatch to disable CSRF check for this view.
        This is necessary because Suno API will call this endpoint without CSRF token.
        """
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """
        Handle callback from Suno API.
        
        Expected payload formats from Suno API:
        1. Simple format:
        {
            "taskId": "string",
            "status": "success|failed|processing",
            "result": {...}
        }
        
        2. Extended format:
        {
            "code": 200,
            "msg": "message",
            "data": {
                "callbackType": "complete|error",
                "task_id": "string",
                "data": [...]
            }
        }
        """
        # Detailed logging of incoming callback request
        try:
            logger.info(
                "Suno callback received: method=%s path=%s query_params=%s",
                request.method,
                request.get_full_path(),
                dict(request.query_params),
            )

            # Headers (redact authorization-like headers if any)
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

            # Raw body (truncated to avoid flooding logs)
            try:
                raw_body = request.body.decode("utf-8", errors="replace")
            except Exception:
                raw_body = "<unreadable body>"

            if len(raw_body) > 4000:
                raw_body_log = raw_body[:4000] + "... [truncated]"
            else:
                raw_body_log = raw_body

            logger.debug("Suno callback raw body: %s", raw_body_log)

            # Parsed data
            logger.debug("Suno callback parsed data: %s", request.data)
        except Exception as log_exc:
            # Never fail the handler because of logging issues
            logger.error("Failed to log Suno callback request: %s", str(log_exc))

        try:
            # Extract task_id from various possible locations in callback data
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
            
            # Find the MusicGeneration instance by task_id
            try:
                instance = MusicGeneration.objects.get(task_id=task_id)
            except MusicGeneration.DoesNotExist:
                logger.warning(f"Callback received for unknown task_id: {task_id}")
                return Response(
                    {'error': 'Task not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Parse the callback data using the callback-specific parser
            suno_service = SunoAPIService()
            parsed_data = suno_service.parse_callback_response(request.data)
            
            # Log parsed data for debugging
            logger.info(f"Parsed callback data for task {task_id}: status={parsed_data.get('status')}, "
                       f"song_1_url={parsed_data.get('song_1_url')}, song_1_stream_url={parsed_data.get('song_1_stream_url')}, "
                       f"song_1_image_url={parsed_data.get('song_1_image_url')}, song_1_duration={parsed_data.get('song_1_duration')}, "
                       f"song_1_tags={parsed_data.get('song_1_tags')}, song_1_model_name={parsed_data.get('song_1_model_name')}")
            
            # Update instance with callback data
            instance.status = parsed_data['status']
            
            # Update song 1 data
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
            
            # Update song 2 data
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
            
            # Send WebSocket update to the user who owns this music generation
            try:
                channel_layer = get_channel_layer()
                if channel_layer:
                    # Serialize the updated instance
                    serializer = MusicGenerationSerializer(instance)
                    
                    # Send update to user's WebSocket group
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
                # Don't fail the callback if WebSocket update fails
                logger.error(f"Error sending WebSocket update: {str(ws_error)}", exc_info=True)
            
            return Response({'status': 'ok'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error processing callback: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for chat endpoints.
    
    Endpoints:
    - GET /api/chat/ - List all chat messages
    - POST /api/chat/ - Create a new chat message
    - GET /api/chat/{id}/ - Get a specific chat message
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Filter queryset by current user.
        Users can only see their own chat messages.
        """
        return ChatMessage.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """
        Automatically assign the current user to the chat message.
        """
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Create a new chat message.
        Currently returns a placeholder response.
        TODO: Integrate with actual chat model/API.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set role to 'user' if not provided
        if 'role' not in serializer.validated_data:
            serializer.validated_data['role'] = 'user'
        
        # Create the message (user is set in perform_create)
        self.perform_create(serializer)
        instance = serializer.instance
        
        # TODO: Generate assistant response here
        # For now, just return the user message
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

