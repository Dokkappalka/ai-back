from django.db import migrations


def seed_ai_models(apps, schema_editor):
    AIModel = apps.get_model('api', 'AIModel')
    models = [
        {
            'model_id': 'deepseek/deepseek-v3.2',
            'name': 'DeepSeek V3.2',
            'is_active': True,
            'is_default': True,
            'order': 0,
        },
        {
            'model_id': 'google/gemini-2.5-flash-image',
            'name': 'Gemini 2.5 Flash Image (Nano Banana)',
            'is_active': True,
            'is_default': False,
            'order': 1,
        },
        {
            'model_id': 'openai/gpt-4o-mini',
            'name': 'GPT-4o Mini',
            'is_active': True,
            'is_default': False,
            'order': 2,
        },
    ]
    for entry in models:
        AIModel.objects.update_or_create(
            model_id=entry['model_id'],
            defaults={
                'name': entry['name'],
                'is_active': entry['is_active'],
                'is_default': entry['is_default'],
                'order': entry['order'],
            },
        )


def unseed_ai_models(apps, schema_editor):
    AIModel = apps.get_model('api', 'AIModel')
    AIModel.objects.filter(model_id__in=[
        'deepseek/deepseek-v3.2',
        'google/gemini-2.5-flash-image',
        'openai/gpt-4o-mini',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_project_models'),
    ]

    operations = [
        migrations.RunPython(seed_ai_models, unseed_ai_models),
    ]
