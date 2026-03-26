# Generated migration for ChatMessageAttachment model

import api.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_aimodel'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChatMessageAttachment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file', models.FileField(help_text='Uploaded file', upload_to=api.models.chat_attachment_upload_path)),
                ('original_filename', models.CharField(help_text='Original filename as uploaded by the user', max_length=255)),
                ('file_type', models.CharField(
                    choices=[('image', 'Image'), ('text', 'Text File'), ('pdf', 'PDF Document'), ('other', 'Other')],
                    default='other',
                    help_text='Type of the attachment',
                    max_length=20,
                )),
                ('mime_type', models.CharField(blank=True, default='', help_text='MIME type of the file (e.g., image/png, text/plain)', max_length=100)),
                ('file_size', models.IntegerField(default=0, help_text='File size in bytes')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('message', models.ForeignKey(
                    help_text='Message this attachment belongs to',
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='attachments',
                    to='api.chatmessage',
                )),
            ],
            options={
                'verbose_name': 'Chat Message Attachment',
                'verbose_name_plural': 'Chat Message Attachments',
                'ordering': ['created_at'],
            },
        ),
    ]
