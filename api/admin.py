from django.contrib import admin
from .models import ImageGeneration, VideoGeneration, MusicGeneration, ChatMessage


@admin.register(ImageGeneration)
class ImageGenerationAdmin(admin.ModelAdmin):
    list_display = ['id', 'prompt', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['prompt']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(VideoGeneration)
class VideoGenerationAdmin(admin.ModelAdmin):
    list_display = ['id', 'prompt', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['prompt']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MusicGeneration)
class MusicGenerationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'model', 'status', 'task_id', 'created_at']
    list_filter = ['status', 'model', 'custom_mode', 'instrumental', 'created_at']
    search_fields = ['prompt', 'title', 'style', 'task_id', 'user__username']
    readonly_fields = ['task_id', 'created_at', 'updated_at']
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Suno API Parameters', {
            'fields': (
                'custom_mode', 'instrumental', 'model', 'prompt', 'style', 'title',
                'persona_id', 'negative_tags', 'vocal_gender',
                'style_weight', 'weirdness_constraint', 'audio_weight'
            )
        }),
        ('Status & Tracking', {
            'fields': ('task_id', 'status')
        }),
        ('Results', {
            'fields': (
                'song_1_url', 'song_1_stream_url',
                'song_2_url', 'song_2_stream_url'
            )
        }),
        ('Error Handling', {
            'fields': ('error_message', 'error_code')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'role', 'content', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content']
    readonly_fields = ['created_at', 'updated_at']

