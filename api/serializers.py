from rest_framework import serializers
from .models import ImageGeneration, VideoGeneration, MusicGeneration, ChatMessage


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
            # Custom Mode validation
            if instrumental:
                # If instrumental is true: style and title are required
                if not data.get('style'):
                    raise serializers.ValidationError({
                        'style': 'Style is required when custom_mode is true and instrumental is true.'
                    })
                if not data.get('title'):
                    raise serializers.ValidationError({
                        'title': 'Title is required when custom_mode is true and instrumental is true.'
                    })
            else:
                # If instrumental is false: style, prompt, and title are required
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
            # Non-custom Mode: only prompt is required
            if not data.get('prompt'):
                raise serializers.ValidationError({
                    'prompt': 'Prompt is required when custom_mode is false.'
                })

        # Validate numeric fields range
        for field_name in ['style_weight', 'weirdness_constraint', 'audio_weight']:
            value = data.get(field_name)
            if value is not None:
                if value < 0 or value > 1:
                    raise serializers.ValidationError({
                        field_name: f'{field_name} must be between 0.00 and 1.00.'
                    })

        return data


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for ChatMessage model.
    """
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'role',
            'content',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'created_at',
            'updated_at',
        ]

