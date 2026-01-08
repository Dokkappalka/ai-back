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


class ChatMessage(models.Model):
    """
    Model for chat messages.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='user'
    )
    content = models.TextField(help_text="Message content")
    # TODO: Add conversation/session field for grouping messages
    # conversation_id = models.CharField(max_length=100, blank=True, null=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        related_name='chat_messages',
        help_text="User who created this message"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Chat Message'
        verbose_name_plural = 'Chat Messages'
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"Chat Message #{self.id} - {self.role}"

