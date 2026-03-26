from django.contrib import admin
from .models import (
    ImageGeneration, VideoGeneration, MusicGeneration,
    AIModel, Conversation, ChatMessage, ChatMessageAttachment,
)


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


@admin.register(AIModel)
class AIModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'model_id', 'name', 'is_active', 'order']
    list_filter = ['is_active']
    search_fields = ['model_id', 'name']
    list_editable = ['is_active', 'order']
    ordering = ['order', 'model_id']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'title', 'model', 'is_archived', 'created_at', 'updated_at']
    list_filter = ['model', 'is_archived', 'created_at']
    search_fields = ['title', 'user__username', 'system_prompt']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Conversation Settings', {
            'fields': ('title', 'model', 'system_prompt', 'temperature', 'max_tokens', 'is_archived')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


class ChatMessageAttachmentInline(admin.TabularInline):
    model = ChatMessageAttachment
    extra = 0
    readonly_fields = ['file', 'original_filename', 'file_type', 'mime_type', 'file_size', 'created_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'user', 'role', 'short_content', 'model', 'tokens_used', 'attachment_count', 'created_at']
    list_filter = ['role', 'model', 'created_at']
    search_fields = ['content', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ChatMessageAttachmentInline]

    def short_content(self, obj):
        return obj.content[:80] + ('...' if len(obj.content) > 80 else '')
    short_content.short_description = 'Content'

    def attachment_count(self, obj):
        return obj.attachments.count()
    attachment_count.short_description = 'Attachments'


@admin.register(ChatMessageAttachment)
class ChatMessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'original_filename', 'file_type', 'mime_type', 'file_size', 'created_at']
    list_filter = ['file_type', 'created_at']
    search_fields = ['original_filename', 'mime_type']
    readonly_fields = ['created_at']
