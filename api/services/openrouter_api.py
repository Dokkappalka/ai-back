"""
Service for interacting with OpenRouter API.
Documentation: https://openrouter.ai/docs/quickstart
"""
import json
import requests
import httpx
import logging
from decouple import config

logger = logging.getLogger(__name__)


def _images_to_markdown(images):
    """Convert OpenRouter images array to inline markdown."""
    parts = []
    for img in images:
        if img.get('type') == 'image_url':
            url = img.get('image_url', {}).get('url', '')
            if url:
                parts.append(f"\n![generated image]({url})\n")
    return ''.join(parts)


from django.core.cache import cache
from api.models import AIModel

DEFAULT_MODEL = 'openai/gpt-4o-mini'


class OpenRouterService:
    """
    Service class for interacting with OpenRouter API for chat completions. Мега пенис, я просто инициирую docker Actions.
    """
    BASE_URL = "https://openrouter.ai/api/v1"
    MODELS_CACHE_KEY = "openrouter_all_models_data"
    MODELS_CACHE_TIMEOUT = 60 * 60 * 24  # Cache for 24 hours

    def __init__(self):
        self.api_key = config('OPENROUTER_API_KEY', default='')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY must be set in environment variables")

    def _get_headers(self):
        """Get headers for API requests."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://unsubordinative-nonbeatifically-macie.ngrok-free.dev',
            'X-OpenRouter-Title': 'AI Hype',
        }

    def chat_completion(self, messages, model=None, temperature=0.7, max_tokens=4096, modalities=None):
        """
        Send a chat completion request to OpenRouter API.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            model: Model ID to use. Defaults to DEFAULT_MODEL.
            temperature: Sampling temperature (0.0 - 2.0). Default 0.7.
            max_tokens: Maximum tokens in response. Default 4096.
            modalities: Optional list of output modalities, e.g. ["image", "text"].

        Returns:
            dict with keys: content, model, usage, finish_reason
        """
        url = f"{self.BASE_URL}/chat/completions"

        payload = {
            'model': model or DEFAULT_MODEL,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
        }
        if modalities:
            payload['modalities'] = modalities

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=120
            )
            response.raise_for_status()
            result = response.json()

            choices = result.get('choices', [])
            if not choices:
                raise ValueError("No choices returned from OpenRouter API")

            first_choice = choices[0]
            message = first_choice.get('message', {})

            content = message.get('content') or ''

            # Handle images in response (OpenRouter image generation)
            images = message.get('images', [])
            if images:
                content += _images_to_markdown(images)

            parsed = {
                'content': content,
                'model': result.get('model', model or DEFAULT_MODEL),
                'usage': result.get('usage', {}),
                'finish_reason': first_choice.get('finish_reason', 'unknown'),
            }

            logger.info(
                f"OpenRouter chat completion successful. "
                f"Model: {parsed['model']}, "
                f"Tokens: {parsed['usage'].get('total_tokens', 'N/A')}"
            )

            return parsed

        except requests.exceptions.Timeout as e:
            error_msg = f"OpenRouter API request timed out after 120 seconds"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = "Failed to connect to OpenRouter API. Check your internet connection."
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
        except requests.exceptions.HTTPError as e:
            error_msg = f"OpenRouter API returned HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_detail = error_data.get('error', {})
                if isinstance(error_detail, dict):
                    error_msg += f": {error_detail.get('message', 'Unknown error')}"
                else:
                    error_msg += f": {error_detail}"
            except Exception:
                error_msg += f": {response.text[:200]}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
        except requests.RequestException as e:
            error_msg = f"OpenRouter API request failed: {str(e)}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e

    def chat_completion_stream(self, messages, model=None, temperature=0.7, max_tokens=4096, modalities=None):
        """
        Send a streaming chat completion request to OpenRouter API (sync version).
        Yields chunks of the response as they arrive.
        """
        url = f"{self.BASE_URL}/chat/completions"

        payload = {
            'model': model or DEFAULT_MODEL,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': True,
        }
        if modalities:
            payload['modalities'] = modalities

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=180,
                stream=True,
            )
            response.raise_for_status()
            response.encoding = 'utf-8'

            yield from self._parse_sse_lines(
                response.iter_lines(chunk_size=1, decode_unicode=True),
                model or DEFAULT_MODEL,
            )

        except requests.exceptions.Timeout:
            yield {'type': 'error', 'content': 'OpenRouter API streaming request timed out after 180 seconds'}
        except requests.exceptions.ConnectionError:
            yield {'type': 'error', 'content': 'Failed to connect to OpenRouter API.'}
        except requests.exceptions.HTTPError:
            error_msg = f"OpenRouter API returned HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_detail = error_data.get('error', {})
                if isinstance(error_detail, dict):
                    error_msg += f": {error_detail.get('message', 'Unknown error')}"
                else:
                    error_msg += f": {error_detail}"
            except Exception:
                error_msg += f": {response.text[:200]}"
            yield {'type': 'error', 'content': error_msg}
        except requests.RequestException as e:
            yield {'type': 'error', 'content': f'OpenRouter API streaming request failed: {str(e)}'}

    async def chat_completion_stream_async(self, messages, model=None, temperature=0.7, max_tokens=4096, modalities=None):
        """
        Async streaming chat completion using httpx.
        Required for Daphne/ASGI to flush chunks incrementally.
        Yields dicts with type='chunk'|'done'|'error'.
        """
        url = f"{self.BASE_URL}/chat/completions"

        payload = {
            'model': model or DEFAULT_MODEL,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': True,
        }
        if modalities:
            payload['modalities'] = modalities

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(180.0, connect=10.0)) as client:
                async with client.stream(
                    'POST',
                    url,
                    json=payload,
                    headers=self._get_headers(),
                ) as response:
                    if response.status_code != 200:
                        body = await response.aread()
                        error_msg = f"OpenRouter API returned HTTP {response.status_code}"
                        try:
                            error_data = json.loads(body)
                            error_detail = error_data.get('error', {})
                            if isinstance(error_detail, dict):
                                error_msg += f": {error_detail.get('message', 'Unknown error')}"
                            else:
                                error_msg += f": {error_detail}"
                        except Exception:
                            error_msg += f": {body.decode('utf-8', errors='replace')[:200]}"
                        logger.error(error_msg)
                        yield {'type': 'error', 'content': error_msg}
                        return

                    used_model = model or DEFAULT_MODEL
                    finish_reason = None
                    usage = {}

                    async for raw_line in response.aiter_lines():
                        line = raw_line.strip()
                        if not line or not line.startswith('data: '):
                            continue

                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            yield {
                                'type': 'done',
                                'content': '',
                                'model': used_model,
                                'usage': usage,
                                'finish_reason': finish_reason or 'stop',
                            }
                            return

                        try:
                            chunk = json.loads(data_str)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse streaming chunk: {data_str[:200]}")
                            continue

                        if chunk.get('model'):
                            used_model = chunk['model']
                        if chunk.get('usage'):
                            usage = chunk['usage']

                        choices = chunk.get('choices', [])
                        if not choices:
                            continue

                        first_choice = choices[0]
                        delta = first_choice.get('delta', {})
                        content = delta.get('content', '') or ''

                        # Handle images in delta (OpenRouter image generation)
                        images = delta.get('images', [])
                        if images:
                            content += _images_to_markdown(images)

                        if first_choice.get('finish_reason'):
                            finish_reason = first_choice['finish_reason']

                        if content:
                            yield {
                                'type': 'chunk',
                                'content': content,
                                'model': used_model,
                            }

                    # If no [DONE] received, still emit done
                    yield {
                        'type': 'done',
                        'content': '',
                        'model': used_model,
                        'usage': usage,
                        'finish_reason': finish_reason or 'stop',
                    }

        except httpx.TimeoutException:
            yield {'type': 'error', 'content': 'OpenRouter API streaming request timed out'}
        except httpx.ConnectError:
            yield {'type': 'error', 'content': 'Failed to connect to OpenRouter API.'}
        except Exception as e:
            logger.error(f"OpenRouter async streaming error: {str(e)}", exc_info=True)
            yield {'type': 'error', 'content': f'OpenRouter API streaming error: {str(e)}'}

    @staticmethod
    def _parse_sse_lines(lines_iter, default_model):
        """Parse SSE lines from a sync iterator. Shared logic for sync streaming."""
        used_model = default_model
        finish_reason = None
        usage = {}

        for line in lines_iter:
            if not line:
                continue
            if not line.startswith('data: '):
                continue

            data_str = line[6:]
            if data_str.strip() == '[DONE]':
                yield {
                    'type': 'done',
                    'content': '',
                    'model': used_model,
                    'usage': usage,
                    'finish_reason': finish_reason or 'stop',
                }
                return

            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse streaming chunk: {data_str[:200]}")
                continue

            if chunk.get('model'):
                used_model = chunk['model']
            if chunk.get('usage'):
                usage = chunk['usage']

            choices = chunk.get('choices', [])
            if not choices:
                continue

            first_choice = choices[0]
            delta = first_choice.get('delta', {})
            content = delta.get('content', '') or ''

            # Handle images in delta (OpenRouter image generation)
            images = delta.get('images', [])
            if images:
                content += _images_to_markdown(images)

            if first_choice.get('finish_reason'):
                finish_reason = first_choice['finish_reason']

            if content:
                yield {
                    'type': 'chunk',
                    'content': content,
                    'model': used_model,
                }

        yield {
            'type': 'done',
            'content': '',
            'model': used_model,
            'usage': usage,
            'finish_reason': finish_reason or 'stop',
        }

    @classmethod
    def _fetch_all_models_metadata(cls):
        """
        Fetch all models metadata from OpenRouter API and cache it.
        Returns a dict mapping model_id -> metadata dict.
        """
        cached_data = cache.get(cls.MODELS_CACHE_KEY)
        if cached_data is not None:
            return cached_data

        try:
            url = f"{cls.BASE_URL}/models"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            metadata_map = {}
            for item in data.get('data', []):
                # Determine model capabilities from architecture/modality info
                architecture = item.get('architecture', {})
                modality = architecture.get('modality', '')
                # modality is like "text->text", "text+image->text", etc.
                input_modalities = modality.split('->')[0] if '->' in modality else ''

                supports_vision = 'image' in input_modalities
                supports_file_input = 'file' in input_modalities

                metadata_map[item['id']] = {
                    'description': item.get('description', ''),
                    'context_length': item.get('context_length', 0),
                    'pricing': item.get('pricing', {}),
                    'supports_vision': supports_vision,
                    'supports_file_input': supports_file_input,
                    'modality': modality,
                }

            cache.set(cls.MODELS_CACHE_KEY, metadata_map, cls.MODELS_CACHE_TIMEOUT)
            return metadata_map
        except Exception as e:
            logger.error(f"Failed to fetch OpenRouter models metadata: {str(e)}")
            return {}

    @classmethod
    def get_available_models(cls):
        """
        Return list of available models configured in the database.
        Enriches model info with dynamic context_length, pricing, and capabilities from OpenRouter API.

        Returns:
            list: List of model dicts with id, name, provider, description,
                  context_length, pricing, supports_vision, supports_file_input, modality
        """
        active_models_db = AIModel.objects.filter(is_active=True).order_by('order', 'model_id')
        
        # If no models in DB, fallback to a sensible default so UI doesn't break
        if not active_models_db.exists():
            return [
                {
                    'id': DEFAULT_MODEL,
                    'name': 'GPT-4o Mini',
                    'provider': 'OpenAI',
                    'description': 'Fallback model. Administrator should add models in the Django Admin.',
                    'context_length': 128000,
                    'pricing': {},
                    'supports_vision': True,
                    'supports_file_input': False,
                    'modality': 'text+image->text',
                    'is_default': True,
                }
            ]

        metadata_map = cls._fetch_all_models_metadata()
        
        models = []
        for db_model in active_models_db:
            model_id = db_model.model_id
            
            provider = 'Unknown'
            if '/' in model_id:
                provider = model_id.split('/')[0].capitalize()

            # Merge DB info with fetched metadata
            meta = metadata_map.get(model_id, {})
            
            models.append({
                'id': model_id,
                'name': db_model.name or model_id,
                'provider': provider,
                'description': meta.get('description', ''),
                'context_length': meta.get('context_length', 0),
                'pricing': meta.get('pricing', {}),
                'supports_vision': meta.get('supports_vision', False),
                'supports_file_input': meta.get('supports_file_input', False),
                'modality': meta.get('modality', 'text->text'),
                'is_default': db_model.is_default,
            })

        return models

    @classmethod
    def is_valid_model(cls, model_id):
        """
        Check if a model ID is valid (exists in AIModel and is active).

        Args:
            model_id: The model ID to validate

        Returns:
            bool: True if valid
        """
        return AIModel.objects.filter(model_id=model_id, is_active=True).exists()
