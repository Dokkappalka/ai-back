from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class ImageGeneration(models.Model):
    """
    Model for image generation requests.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    prompt = models.TextField(help_text="Text prompt for image generation")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    result_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to the generated image"
    )
    result_file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to the generated image file"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if generation failed"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='image_generations',
        help_text="User who created this generation request"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Image Generation'
        verbose_name_plural = 'Image Generations'
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Image Generation #{self.id} - {self.status}"


class VideoGeneration(models.Model):
    """
    Model for video generation requests.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    prompt = models.TextField(help_text="Text prompt for video generation")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    result_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to the generated video"
    )
    result_file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Path to the generated video file"
    )
    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if generation failed"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='video_generations',
        help_text="User who created this generation request"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Video Generation'
        verbose_name_plural = 'Video Generations'
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Video Generation #{self.id} - {self.status}"


class MusicGeneration(models.Model):
    """
    Model for music generation requests using Suno API.
    Each request generates 2 songs.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    MODEL_CHOICES = [
        ('V4', 'V4'),
        ('V4_5', 'V4.5'),
        ('V4_5PLUS', 'V4.5+'),
        ('V4_5ALL', 'V4.5 All'),
        ('V5', 'V5'),
    ]

    VOCAL_GENDER_CHOICES = [
        ('m', 'Male'),
        ('f', 'Female'),
    ]

    # User association - для разделения запросов по пользователям
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='music_generations',
        help_text="User who created this generation request"
    )

    # Suno API parameters
    custom_mode = models.BooleanField(
        default=False,
        help_text="Enable Custom Mode for advanced audio generation settings"
    )
    instrumental = models.BooleanField(
        default=False,
        help_text="Determines if the audio should be instrumental (no lyrics)"
    )
    model = models.CharField(
        max_length=20,
        choices=MODEL_CHOICES,
        default='V4_5ALL',
        help_text="The model version to use for audio generation"
    )
    prompt = models.TextField(
        blank=True,
        null=True,
        help_text="Text prompt for music generation (required in certain modes)"
    )
    style = models.CharField(
        max_length=1000,
        blank=True,
        null=True,
        help_text="The music style or genre for the audio"
    )
    title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="The title of the generated music track"
    )
    persona_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Persona ID to apply to the generated music"
    )
    negative_tags = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Music styles or traits to exclude from the generated audio"
    )
    vocal_gender = models.CharField(
        max_length=1,
        choices=VOCAL_GENDER_CHOICES,
        blank=True,
        null=True,
        help_text="Preferred vocal gender for generated vocals"
    )
    style_weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Weight of the provided style guidance (0.00-1.00)"
    )
    weirdness_constraint = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Constraint on creative deviation/novelty (0.00-1.00)"
    )
    audio_weight = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Weight of the input audio influence (0.00-1.00)"
    )

    # Suno API response tracking
    task_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        unique=True,
        help_text="Suno API task ID for tracking generation status"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Results (Suno API returns 2 songs)
    song_1_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to the first generated song"
    )
    song_1_stream_url = models.URLField(
        blank=True,
        null=True,
        help_text="Stream URL for the first song (available in 30-40 seconds)"
    )
    song_1_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Suno API unique identifier for the first song"
    )
    song_1_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Cover image URL for the first song"
    )
    song_1_duration = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Duration of the first song in seconds"
    )
    song_1_tags = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Tags for the first song"
    )
    song_1_model_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Model name used for the first song"
    )
    song_2_url = models.URLField(
        blank=True,
        null=True,
        help_text="URL to the second generated song"
    )
    song_2_stream_url = models.URLField(
        blank=True,
        null=True,
        help_text="Stream URL for the second song (available in 30-40 seconds)"
    )
    song_2_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Suno API unique identifier for the second song"
    )
    song_2_image_url = models.URLField(
        blank=True,
        null=True,
        help_text="Cover image URL for the second song"
    )
    song_2_duration = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Duration of the second song in seconds"
    )
    song_2_tags = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Tags for the second song"
    )
    song_2_model_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Model name used for the second song"
    )

    error_message = models.TextField(
        blank=True,
        null=True,
        help_text="Error message if generation failed"
    )
    error_code = models.IntegerField(
        blank=True,
        null=True,
        help_text="Error code from Suno API if generation failed"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Music Generation'
        verbose_name_plural = 'Music Generations'
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['task_id']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        user_str = f"User {self.user.id}" if self.user else "Anonymous"
        return f"Music Generation #{self.id} - {user_str} - {self.status}"


class AIModel(models.Model):
    """
    Model for managing which AI models are available in the frontend.
    Administrators can enable/disable specific OpenRouter models here.
    """
    model_id = models.CharField(
        max_length=150,
        unique=True,
        help_text="Exact Model ID from OpenRouter (e.g., 'openai/gpt-4o-mini')"
    )
    name = models.CharField(
        max_length=150,
        blank=True,
        help_text="Custom name to display. Leave blank to use OpenRouter's default name"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this model is available for users to select"
    )
    is_default = models.BooleanField(
        default=False,
        help_text="Whether this model is selected by default for new chats"
    )
    order = models.IntegerField(
        default=0,
        help_text="Display order in the frontend (lower means higher up)"
    )

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other models to not default
            AIModel.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['order', 'model_id']
        verbose_name = 'AI Model'
        verbose_name_plural = 'AI Models'

    def __str__(self):
        return f"{self.name or self.model_id} ({'Active' if self.is_active else 'Inactive'})"


class Conversation(models.Model):
    """
    Model for chat conversations (sessions).
    Each conversation groups multiple messages together.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations',
        help_text="User who owns this conversation"
    )
    title = models.CharField(
        max_length=255,
        default='New Chat',
        help_text="Title of the conversation"
    )
    model = models.CharField(
        max_length=100,
        default='openai/gpt-4o-mini',
        help_text="OpenRouter model ID used in this conversation"
    )
    system_prompt = models.TextField(
        blank=True,
        null=True,
        help_text="System prompt for this conversation"
    )
    temperature = models.FloatField(
        default=0.7,
        help_text="Sampling temperature (0.0 - 2.0)"
    )
    max_tokens = models.IntegerField(
        default=4096,
        help_text="Maximum tokens in response"
    )
    is_archived = models.BooleanField(
        default=False,
        help_text="Whether this conversation is archived"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        indexes = [
            models.Index(fields=['user', '-updated_at']),
            models.Index(fields=['user', 'is_archived']),
        ]

    def __str__(self):
        return f"Conversation #{self.id} - {self.title}"


class ChatMessage(models.Model):
    """
    Model for chat messages within a conversation.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages',
        help_text="Conversation this message belongs to"
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user'
    )
    content = models.TextField(help_text="Message content")
    model = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Model that generated this message (for assistant messages)"
    )
    tokens_used = models.IntegerField(
        blank=True,
        null=True,
        help_text="Total tokens used for this response"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='chat_messages',
        help_text="User who owns this message"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Message #{self.id} - {self.role} in Conv #{self.conversation_id}"


def chat_attachment_upload_path(instance, filename):
    """Generate upload path for chat attachments: chat_attachments/<user_id>/<conversation_id>/<filename>"""
    return f"chat_attachments/{instance.message.user_id}/{instance.message.conversation_id}/{filename}"


class ChatMessageAttachment(models.Model):
    """
    Model for file attachments on chat messages.
    Supports images, text files, PDFs, and other documents.
    Files are converted to the appropriate format for the OpenRouter API
    (e.g., base64 data URLs for images sent to vision models).
    """
    ATTACHMENT_TYPE_CHOICES = [
        ('image', 'Image'),
        ('text', 'Text File'),
        ('pdf', 'PDF Document'),
        ('other', 'Other'),
    ]

    message = models.ForeignKey(
        ChatMessage,
        on_delete=models.CASCADE,
        related_name='attachments',
        help_text="Message this attachment belongs to"
    )
    file = models.FileField(
        upload_to=chat_attachment_upload_path,
        help_text="Uploaded file"
    )
    original_filename = models.CharField(
        max_length=255,
        help_text="Original filename as uploaded by the user"
    )
    file_type = models.CharField(
        max_length=20,
        choices=ATTACHMENT_TYPE_CHOICES,
        default='other',
        help_text="Type of the attachment"
    )
    mime_type = models.CharField(
        max_length=100,
        blank=True,
        default='',
        help_text="MIME type of the file (e.g., image/png, text/plain)"
    )
    file_size = models.IntegerField(
        default=0,
        help_text="File size in bytes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Chat Message Attachment'
        verbose_name_plural = 'Chat Message Attachments'

    def __str__(self):
        return f"Attachment '{self.original_filename}' on Message #{self.message_id}"

    @property
    def is_image(self):
        return self.file_type == 'image'

    @property
    def is_text(self):
        return self.file_type in ('text', 'pdf')

