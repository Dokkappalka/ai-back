from rest_framework import serializers
from .models import (
    ImageGeneration, VideoGeneration, MusicGeneration,
    Conversation, ChatMessage, ChatMessageAttachment,
    Project, ProjectTrack, ProjectChatMessage,
)


class ImageGenerationSerializer(serializers.ModelSerializer):
    """
    Serializer for ImageGeneration model.
    """
    class Meta:
        model = ImageGeneration
        fields = [
            'id',
            'prompt',
            'status',
            'result_url',
            'result_file_path',
            'error_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'result_url',
            'result_file_path',
            'error_message',
            'created_at',
            'updated_at',
        ]


class VideoGenerationSerializer(serializers.ModelSerializer):
    """
    Serializer for VideoGeneration model.
    """
    class Meta:
        model = VideoGeneration
        fields = [
            'id',
            'prompt',
            'status',
            'result_url',
            'result_file_path',
            'error_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'status',
            'result_url',
            'result_file_path',
            'error_message',
            'created_at',
            'updated_at',
        ]


class MusicGenerationSerializer(serializers.ModelSerializer):
    """
    Serializer for MusicGeneration model (Suno API integration).
    """
    user = serializers.PrimaryKeyRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = MusicGeneration
        fields = [
            'id',
            'user',
            # Suno API parameters
            'custom_mode',
            'instrumental',
            'model',
            'prompt',
            'style',
            'title',
            'persona_id',
            'negative_tags',
            'vocal_gender',
            'style_weight',
            'weirdness_constraint',
            'audio_weight',
            # Status and tracking
            'task_id',
            'status',
            # Results
            'song_1_url',
            'song_1_stream_url',
            'song_1_id',
            'song_1_image_url',
            'song_1_duration',
            'song_1_tags',
            'song_1_model_name',
            'song_2_url',
            'song_2_stream_url',
            'song_2_id',
            'song_2_image_url',
            'song_2_duration',
            'song_2_tags',
            'song_2_model_name',
            # Error handling
            'error_message',
            'error_code',
            # Timestamps
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user',
            'task_id',
            'status',
            'song_1_url',
            'song_1_stream_url',
            'song_1_id',
            'song_1_image_url',
            'song_1_duration',
            'song_1_tags',
            'song_1_model_name',
            'song_2_url',
            'song_2_stream_url',
            'song_2_id',
            'song_2_image_url',
            'song_2_duration',
            'song_2_tags',
            'song_2_model_name',
            'error_message',
            'error_code',
            'created_at',
            'updated_at',
        ]

    def validate(self, data):
        """
        Validate Suno API parameters based on custom_mode and instrumental settings.
        """
        custom_mode = data.get('custom_mode', False)
        instrumental = data.get('instrumental', False)

        if custom_mode:
            if instrumental:
                if not data.get('style'):
                    raise serializers.ValidationError({
                        'style': 'Style is required when custom_mode is true and instrumental is true.'
                    })
                if not data.get('title'):
                    raise serializers.ValidationError({
                        'title': 'Title is required when custom_mode is true and instrumental is true.'
                    })
            else:
                if not data.get('style'):
                    raise serializers.ValidationError({
                        'style': 'Style is required when custom_mode is true and instrumental is false.'
                    })
                if not data.get('prompt'):
                    raise serializers.ValidationError({
                        'prompt': 'Prompt is required when custom_mode is true and instrumental is false.'
                    })
                if not data.get('title'):
                    raise serializers.ValidationError({
                        'title': 'Title is required when custom_mode is true and instrumental is false.'
                    })
        else:
            if not data.get('prompt'):
                raise serializers.ValidationError({
                    'prompt': 'Prompt is required when custom_mode is false.'
                })

        for field_name in ['style_weight', 'weirdness_constraint', 'audio_weight']:
            value = data.get(field_name)
            if value is not None:
                if value < 0 or value > 1:
                    raise serializers.ValidationError({
                        field_name: f'{field_name} must be between 0.00 and 1.00.'
                    })

        return data


class ChatMessageAttachmentSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatMessageAttachment model.
    """
    url = serializers.SerializerMethodField()

    class Meta:
        model = ChatMessageAttachment
        fields = [
            'id',
            'message',
            'file',
            'original_filename',
            'file_type',
            'mime_type',
            'file_size',
            'url',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'file_type',
            'mime_type',
            'file_size',
            'url',
            'created_at',
        ]

    def get_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        elif obj.file:
            return obj.file.url
        return None


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatMessage model.
    Includes nested attachments.
    """
    attachments = ChatMessageAttachmentSerializer(many=True, read_only=True)

    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'conversation',
            'role',
            'content',
            'model',
            'tokens_used',
            'attachments',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'model',
            'tokens_used',
            'attachments',
            'created_at',
            'updated_at',
        ]


class ConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Conversation model.
    """
    message_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'title',
            'model',
            'system_prompt',
            'temperature',
            'max_tokens',
            'is_archived',
            'message_count',
            'last_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'message_count',
            'last_message',
            'created_at',
            'updated_at',
        ]

    def get_message_count(self, obj):
        return obj.messages.count()

    def get_last_message(self, obj):
        last = obj.messages.order_by('-created_at').first()
        if last:
            return {
                'id': last.id,
                'role': last.role,
                'content': last.content[:100] + ('...' if len(last.content) > 100 else ''),
                'created_at': last.created_at.isoformat(),
            }
        return None

    def validate_model(self, value):
        from .services.openrouter_api import OpenRouterService
        if not OpenRouterService.is_valid_model(value):
            raise serializers.ValidationError(
                f"Unknown model '{value}'. Use GET /api/chat/models/ to see available models."
            )
        return value

    def validate_temperature(self, value):
        if value < 0.0 or value > 2.0:
            raise serializers.ValidationError("Temperature must be between 0.0 and 2.0.")
        return value

    def validate_max_tokens(self, value):
        if value < 1 or value > 128000:
            raise serializers.ValidationError("max_tokens must be between 1 and 128000.")
        return value


class ProjectChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectChatMessage
        fields = ['id', 'project', 'role', 'content', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProjectTrackSerializer(serializers.ModelSerializer):
    music_generation_data = MusicGenerationSerializer(source='music_generation', read_only=True)

    class Meta:
        model = ProjectTrack
        fields = [
            'id', 'project', 'order', 'title',
            'suno_prompt', 'suno_style', 'suno_model',
            'suno_instrumental', 'suno_negative_tags',
            'music_generation', 'music_generation_data',
            'selected_song', 'status',
        ]
        read_only_fields = ['id', 'project', 'music_generation_data']


class ProjectSerializer(serializers.ModelSerializer):
    tracks = ProjectTrackSerializer(many=True, read_only=True)
    chat_messages = ProjectChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Project
        fields = [
            'id', 'user', 'title', 'type', 'track_count',
            'concept', 'status', 'tracks', 'chat_messages',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'user', 'status', 'tracks', 'chat_messages', 'created_at', 'updated_at']


class ProjectListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for project list (no tracks/messages)."""
    track_count_completed = serializers.SerializerMethodField()
    track_count_with_audio = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            'id', 'title', 'type', 'track_count',
            'track_count_completed', 'track_count_with_audio', 'concept', 'status',
            'created_at', 'updated_at',
        ]

    def get_track_count_completed(self, obj):
        return obj.tracks.filter(status='completed').count()

    def get_track_count_with_audio(self, obj):
        return obj.tracks.filter(status='completed', music_generation__isnull=False).count()


class SendMessageSerializer(serializers.Serializer):
    """
    Serializer for sending a message to a conversation.
    Used for POST /api/chat/conversations/{id}/send_message/

    Supports multipart/form-data for file uploads.
    Files are sent as 'files' field (multiple files allowed).
    """
    content = serializers.CharField(required=True, help_text="Message content")
    files = serializers.ListField(
        child=serializers.FileField(),
        required=False,
        help_text="Optional list of file attachments (images, text files, PDFs, etc.)"
    )
