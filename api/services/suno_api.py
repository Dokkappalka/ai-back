"""
Service for interacting with Suno API.
Documentation: https://docs.sunoapi.org/suno-api/generate-music
"""
import requests
import logging
from django.conf import settings
from decouple import config

logger = logging.getLogger(__name__)


class SunoAPIService:
    """
    Service class for interacting with Suno API for music generation.
    """
    BASE_URL = "https://api.sunoapi.org/api/v1"
    
    def __init__(self):
        self.api_key = config('SUNO_API_KEY', default='')
        if not self.api_key:
            raise ValueError("SUNO_API_KEY must be set in environment variables")
    
    def _get_headers(self):
        """Get headers for API requests."""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
        }
    
    def generate_music(self, **kwargs):
        """
        Generate music using Suno API.
        
        Args:
            **kwargs: Parameters for music generation (custom_mode, instrumental, model, etc.)
        
        Returns:
            dict: Response from Suno API containing task_id
        
        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.BASE_URL}/generate"
        
        # Prepare request payload
        payload = {
            'customMode': kwargs.get('custom_mode', False),
            'instrumental': kwargs.get('instrumental', False),
            'model': kwargs.get('model', 'V4_5ALL'),
        }
        
        # Add optional parameters if provided
        # Map Python parameter names to API parameter names
        param_mapping = {
            'prompt': 'prompt',
            'style': 'style',
            'title': 'title',
            'persona_id': 'personaId',
            'personaId': 'personaId',  # Support both formats
            'negative_tags': 'negativeTags',
            'negativeTags': 'negativeTags',
            'vocal_gender': 'vocalGender',
            'vocalGender': 'vocalGender',
            'style_weight': 'styleWeight',
            'styleWeight': 'styleWeight',
            'weirdness_constraint': 'weirdnessConstraint',
            'weirdnessConstraint': 'weirdnessConstraint',
            'audio_weight': 'audioWeight',
            'audioWeight': 'audioWeight',
        }
        
        for python_param, api_param in param_mapping.items():
            value = kwargs.get(python_param)
            if value is not None:
                payload[api_param] = value
        
        # Add callback URL if provided
        callback_url = kwargs.get('callback_url')
        if callback_url:
            payload['callBackUrl'] = callback_url
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Log successful request
            logger.info(f"Successfully called Suno API generate endpoint. Response code: {result.get('code')}")
            
            return result
        except requests.exceptions.Timeout as e:
            error_msg = f"Suno API request timed out after 30 seconds. URL: {url}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Failed to connect to Suno API. Check your internet connection. URL: {url}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
        except requests.exceptions.HTTPError as e:
            # Try to extract error message from response
            error_msg = f"Suno API returned HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('msg', error_data.get('message', 'Unknown error'))}"
            except:
                error_msg += f": {response.text[:200]}"
            logger.error(f"{error_msg}. URL: {url}")
            raise requests.RequestException(error_msg) from e
        except requests.RequestException as e:
            error_msg = f"Suno API request failed: {str(e)}. URL: {url}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
    
    def get_generation_details(self, task_id):
        """
        Get details about a music generation task.
        
        Args:
            task_id: The task ID returned from generate_music
        
        Returns:
            dict: Response from Suno API containing generation status and results
        
        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.BASE_URL}/generate/record-info"
        
        try:
            response = requests.get(
                url,
                params={'taskId': task_id},
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Log successful request
            logger.debug(f"Successfully called Suno API get_generation_details for task {task_id}")
            
            return result
        except requests.exceptions.Timeout as e:
            error_msg = f"Suno API request timed out after 30 seconds. Task ID: {task_id}, URL: {url}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Failed to connect to Suno API. Check your internet connection. Task ID: {task_id}, URL: {url}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
        except requests.exceptions.HTTPError as e:
            # Try to extract error message from response
            error_msg = f"Suno API returned HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('msg', error_data.get('message', 'Unknown error'))}"
            except:
                error_msg += f": {response.text[:200]}"
            logger.error(f"{error_msg}. Task ID: {task_id}, URL: {url}")
            raise requests.RequestException(error_msg) from e
        except requests.RequestException as e:
            error_msg = f"Suno API request failed: {str(e)}. Task ID: {task_id}, URL: {url}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
    
    def get_remaining_credits(self):
        """
        Get remaining API credits.
        
        Returns:
            dict: Response containing remaining credits
        
        Raises:
            requests.RequestException: If API request fails
        """
        url = f"{self.BASE_URL}/get/credits"
        
        try:
            response = requests.get(
                url,
                headers=self._get_headers(),
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            # Log successful request
            logger.debug("Successfully called Suno API get_remaining_credits endpoint")
            
            return result
        except requests.exceptions.Timeout as e:
            error_msg = f"Suno API request timed out after 30 seconds. URL: {url}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Failed to connect to Suno API. Check your internet connection. URL: {url}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
        except requests.exceptions.HTTPError as e:
            # Try to extract error message from response
            error_msg = f"Suno API returned HTTP {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('msg', error_data.get('message', 'Unknown error'))}"
            except:
                error_msg += f": {response.text[:200]}"
            logger.error(f"{error_msg}. URL: {url}")
            raise requests.RequestException(error_msg) from e
        except requests.RequestException as e:
            error_msg = f"Suno API request failed: {str(e)}. URL: {url}"
            logger.error(error_msg)
            raise requests.RequestException(error_msg) from e
    
    def parse_generation_response(self, api_response):
        """
        Parse the response from get_generation_details() and extract relevant information.
        
        According to Suno API documentation:
        - Status values: PENDING, TEXT_SUCCESS, FIRST_SUCCESS, SUCCESS, CREATE_TASK_FAILED,
          GENERATE_AUDIO_FAILED, CALLBACK_EXCEPTION, SENSITIVE_WORD_ERROR
        
        Args:
            api_response: Raw response from get_generation_details()
        
        Returns:
            dict: Parsed data with keys:
                - status: 'processing', 'completed', or 'failed'
                - song_1_url: URL to first song (if available)
                - song_1_stream_url: Stream URL for first song (if available)
                - song_1_id: Unique identifier for first song (if available)
                - song_1_image_url: Cover image URL for first song (if available)
                - song_1_duration: Duration of first song in seconds (if available)
                - song_1_tags: Tags for first song (if available)
                - song_1_model_name: Model name used for first song (if available)
                - song_2_url: URL to second song (if available)
                - song_2_stream_url: Stream URL for second song (if available)
                - song_2_id: Unique identifier for second song (if available)
                - song_2_image_url: Cover image URL for second song (if available)
                - song_2_duration: Duration of second song in seconds (if available)
                - song_2_tags: Tags for second song (if available)
                - song_2_model_name: Model name used for second song (if available)
                - error_message: Error message (if failed)
                - error_code: Error code (if failed)
        """
        parsed = {
            'status': 'processing',
            'song_1_url': None,
            'song_1_stream_url': None,
            'song_1_id': None,
            'song_1_image_url': None,
            'song_1_duration': None,
            'song_1_tags': None,
            'song_1_model_name': None,
            'song_2_url': None,
            'song_2_stream_url': None,
            'song_2_id': None,
            'song_2_image_url': None,
            'song_2_duration': None,
            'song_2_tags': None,
            'song_2_model_name': None,
            'error_message': None,
            'error_code': None,
        }
        
        # Check if response indicates an error
        if api_response.get('code') != 200:
            parsed['status'] = 'failed'
            parsed['error_message'] = api_response.get('msg', 'Unknown error from Suno API')
            parsed['error_code'] = api_response.get('code', 500)
            logger.warning(f"Suno API error: {parsed['error_message']} (code: {parsed['error_code']})")
            return parsed
        
        data = api_response.get('data', {})
        
        # Get status from API response according to documentation
        api_status = data.get('status', '').upper()
        
        # Check for error statuses
        if api_status in ['CREATE_TASK_FAILED', 'GENERATE_AUDIO_FAILED', 'CALLBACK_EXCEPTION', 'SENSITIVE_WORD_ERROR']:
            parsed['status'] = 'failed'
            parsed['error_message'] = data.get('errorMessage') or data.get('error_message') or f'Generation failed with status: {api_status}'
            parsed['error_code'] = data.get('errorCode') or data.get('error_code')
            logger.error(f"Generation failed: {parsed['error_message']} (status: {api_status})")
            return parsed
        
        # Check if generation is complete
        if api_status == 'SUCCESS':
            parsed['status'] = 'completed'
            
            # Extract songs from response.sunoData array according to documentation
            response_data = data.get('response', {})
            suno_data = response_data.get('sunoData', [])
            
            # Extract song data from sunoData array
            # Suno API typically returns 2 songs
            if len(suno_data) >= 1:
                song1 = suno_data[0]
                parsed['song_1_url'] = song1.get('audioUrl') or song1.get('audio_url')
                parsed['song_1_stream_url'] = song1.get('streamAudioUrl') or song1.get('stream_audio_url')
                parsed['song_1_id'] = song1.get('id')
                parsed['song_1_image_url'] = song1.get('imageUrl') or song1.get('image_url')
                parsed['song_1_duration'] = song1.get('duration')
                parsed['song_1_tags'] = song1.get('tags')
                parsed['song_1_model_name'] = song1.get('modelName') or song1.get('model_name')
            
            if len(suno_data) >= 2:
                song2 = suno_data[1]
                parsed['song_2_url'] = song2.get('audioUrl') or song2.get('audio_url')
                parsed['song_2_stream_url'] = song2.get('streamAudioUrl') or song2.get('stream_audio_url')
                parsed['song_2_id'] = song2.get('id')
                parsed['song_2_image_url'] = song2.get('imageUrl') or song2.get('image_url')
                parsed['song_2_duration'] = song2.get('duration')
                parsed['song_2_tags'] = song2.get('tags')
                parsed['song_2_model_name'] = song2.get('modelName') or song2.get('model_name')
            
            logger.info(f"Successfully parsed generation response: {len(suno_data)} songs found")
            
        elif api_status in ['TEXT_SUCCESS', 'FIRST_SUCCESS']:
            # Partial success - still processing
            parsed['status'] = 'processing'
            logger.debug(f"Generation in progress (status: {api_status})")
            
            # Try to extract any available songs
            response_data = data.get('response', {})
            suno_data = response_data.get('sunoData', [])
            
            if len(suno_data) >= 1:
                song1 = suno_data[0]
                if song1.get('audioUrl') or song1.get('audio_url'):
                    parsed['song_1_url'] = song1.get('audioUrl') or song1.get('audio_url')
                    parsed['song_1_stream_url'] = song1.get('streamAudioUrl') or song1.get('stream_audio_url')
                    parsed['song_1_id'] = song1.get('id')
                    parsed['song_1_image_url'] = song1.get('imageUrl') or song1.get('image_url')
                    parsed['song_1_duration'] = song1.get('duration')
                    parsed['song_1_tags'] = song1.get('tags')
                    parsed['song_1_model_name'] = song1.get('modelName') or song1.get('model_name')
            
            if len(suno_data) >= 2:
                song2 = suno_data[1]
                if song2.get('audioUrl') or song2.get('audio_url'):
                    parsed['song_2_url'] = song2.get('audioUrl') or song2.get('audio_url')
                    parsed['song_2_stream_url'] = song2.get('streamAudioUrl') or song2.get('stream_audio_url')
                    parsed['song_2_id'] = song2.get('id')
                    parsed['song_2_image_url'] = song2.get('imageUrl') or song2.get('image_url')
                    parsed['song_2_duration'] = song2.get('duration')
                    parsed['song_2_tags'] = song2.get('tags')
                    parsed['song_2_model_name'] = song2.get('modelName') or song2.get('model_name')
            
        elif api_status == 'PENDING':
            # Still processing
            parsed['status'] = 'processing'
            logger.debug(f"Generation still pending (status: {api_status})")
        else:
            # Unknown status - assume processing
            parsed['status'] = 'processing'
            logger.warning(f"Unknown status from Suno API: {api_status}, assuming processing")
        
        return parsed
    
    def parse_callback_response(self, callback_data):
        """
        Parse the callback data received from Suno API webhook.
        
        According to Suno API callback documentation (https://docs.sunoapi.org/suno-api/generate-music-callbacks):
        The format is:
        {
            "code": 200,
            "msg": "message",
            "data": {
                "callbackType": "complete|error|text|first",
                "task_id": "string",
                "data": [
                    {
                        "id": "string",
                        "audio_url": "string",           # Main audio file URL
                        "stream_audio_url": "string",    # Streaming audio URL
                        "source_audio_url": "string",
                        "source_stream_audio_url": "string",
                        "image_url": "string",
                        "source_image_url": "string",
                        "prompt": "string",
                        "model_name": "string",
                        "title": "string",
                        "tags": "string",
                        "createTime": "string",
                        "duration": number
                    }
                ]
            }
        }
        
        Args:
            callback_data: Raw callback data from Suno API webhook
        
        Returns:
            dict: Parsed data with keys:
                - status: 'processing', 'completed', or 'failed'
                - song_1_url: URL to first song (if available)
                - song_1_stream_url: Stream URL for first song (if available)
                - song_1_id: Unique identifier for first song (if available)
                - song_1_image_url: Cover image URL for first song (if available)
                - song_1_duration: Duration of first song in seconds (if available)
                - song_1_tags: Tags for first song (if available)
                - song_1_model_name: Model name used for first song (if available)
                - song_2_url: URL to second song (if available)
                - song_2_stream_url: Stream URL for second song (if available)
                - song_2_id: Unique identifier for second song (if available)
                - song_2_image_url: Cover image URL for second song (if available)
                - song_2_duration: Duration of second song in seconds (if available)
                - song_2_tags: Tags for second song (if available)
                - song_2_model_name: Model name used for second song (if available)
                - error_message: Error message (if failed)
                - error_code: Error code (if failed)
        """
        parsed = {
            'status': 'processing',
            'song_1_url': None,
            'song_1_stream_url': None,
            'song_1_id': None,
            'song_1_image_url': None,
            'song_1_duration': None,
            'song_1_tags': None,
            'song_1_model_name': None,
            'song_2_url': None,
            'song_2_stream_url': None,
            'song_2_id': None,
            'song_2_image_url': None,
            'song_2_duration': None,
            'song_2_tags': None,
            'song_2_model_name': None,
            'error_message': None,
            'error_code': None,
        }
        
        # Handle extended format with code/msg/data structure (official format)
        if 'code' in callback_data:
            code = callback_data.get('code')
            if code != 200:
                parsed['status'] = 'failed'
                parsed['error_message'] = callback_data.get('msg', 'Unknown error from Suno API')
                parsed['error_code'] = code
                logger.warning(f"Suno API callback error: {parsed['error_message']} (code: {code})")
                return parsed
            
            # Extract data from extended format
            data = callback_data.get('data', {})
            callback_type = data.get('callbackType', '').lower()
            
            if callback_type == 'error':
                parsed['status'] = 'failed'
                parsed['error_message'] = data.get('errorMessage') or data.get('error_message') or callback_data.get('msg', 'Generation failed')
                parsed['error_code'] = data.get('errorCode') or data.get('error_code') or code
                logger.error(f"Generation failed in callback: {parsed['error_message']}")
                return parsed
            
            # Handle success/completion
            # According to docs: callbackType can be "text", "first", "complete", or "error"
            if callback_type in ['complete', 'success']:
                parsed['status'] = 'completed'
            elif callback_type in ['text', 'first']:
                # Partial completion - still processing
                parsed['status'] = 'processing'
            else:
                # Unknown callback type - assume processing
                parsed['status'] = 'processing'
            
            # Extract songs from data.data array
            songs_data = data.get('data', [])
            
            # According to documentation, extract all available fields
            if len(songs_data) >= 1:
                song1 = songs_data[0]
                # Audio URLs - try all possible field names
                parsed['song_1_url'] = song1.get('audio_url') or song1.get('audioUrl') or song1.get('musicUrl') or song1.get('music_url') or song1.get('url')
                parsed['song_1_stream_url'] = song1.get('stream_audio_url') or song1.get('streamAudioUrl') or song1.get('streamUrl')
                # Additional metadata from callback
                parsed['song_1_id'] = song1.get('id')
                parsed['song_1_image_url'] = song1.get('image_url') or song1.get('imageUrl')
                parsed['song_1_duration'] = song1.get('duration')
                parsed['song_1_tags'] = song1.get('tags')
                parsed['song_1_model_name'] = song1.get('model_name') or song1.get('modelName')
                
                # Log for debugging
                logger.debug(f"Song 1 parsed - audio_url: {parsed['song_1_url']}, stream_url: {parsed['song_1_stream_url']}, "
                           f"image_url: {parsed['song_1_image_url']}, duration: {parsed['song_1_duration']}, "
                           f"tags: {parsed['song_1_tags']}, model: {parsed['song_1_model_name']}")
            
            if len(songs_data) >= 2:
                song2 = songs_data[1]
                # Audio URLs - try all possible field names
                parsed['song_2_url'] = song2.get('audio_url') or song2.get('audioUrl') or song2.get('musicUrl') or song2.get('music_url') or song2.get('url')
                parsed['song_2_stream_url'] = song2.get('stream_audio_url') or song2.get('streamAudioUrl') or song2.get('streamUrl')
                # Additional metadata from callback
                parsed['song_2_id'] = song2.get('id')
                parsed['song_2_image_url'] = song2.get('image_url') or song2.get('imageUrl')
                parsed['song_2_duration'] = song2.get('duration')
                parsed['song_2_tags'] = song2.get('tags')
                parsed['song_2_model_name'] = song2.get('model_name') or song2.get('modelName')
                
                # Log for debugging
                logger.debug(f"Song 2 parsed - audio_url: {parsed['song_2_url']}, stream_url: {parsed['song_2_stream_url']}, "
                           f"image_url: {parsed['song_2_image_url']}, duration: {parsed['song_2_duration']}, "
                           f"tags: {parsed['song_2_tags']}, model: {parsed['song_2_model_name']}")
            
            logger.info(f"Successfully parsed callback: {len(songs_data)} songs found, callbackType: {callback_type}")
            
            return parsed
        
        # Handle simple format with taskId/status/result (legacy/fallback format)
        status = callback_data.get('status', '').lower()
        
        if status == 'failed' or status == 'error':
            parsed['status'] = 'failed'
            parsed['error_message'] = callback_data.get('errorMessage') or callback_data.get('error_message') or callback_data.get('msg', 'Generation failed')
            parsed['error_code'] = callback_data.get('errorCode') or callback_data.get('error_code', 500)
            logger.error(f"Generation failed in callback: {parsed['error_message']}")
            return parsed
        
        if status == 'success' or status == 'completed' or status == 'complete':
            parsed['status'] = 'completed'
            
            # Extract songs from result
            result = callback_data.get('result', {})
            songs_data = result.get('data', []) if isinstance(result, dict) and 'data' in result else []
            
            # If result is a list, use it directly
            if isinstance(result, list):
                songs_data = result
            # If result has songs array
            elif isinstance(result, dict) and 'songs' in result:
                songs_data = result['songs']
            
            if len(songs_data) >= 1:
                song1 = songs_data[0]
                # Try documentation format first, then fallback to other formats
                parsed['song_1_url'] = song1.get('audio_url') or song1.get('audioUrl') or song1.get('musicUrl') or song1.get('music_url') or song1.get('url')
                parsed['song_1_stream_url'] = song1.get('stream_audio_url') or song1.get('streamAudioUrl') or song1.get('stream_audio_url') or song1.get('streamUrl')
                # Additional metadata (legacy format support)
                parsed['song_1_id'] = song1.get('id')
                parsed['song_1_image_url'] = song1.get('image_url') or song1.get('imageUrl')
                parsed['song_1_duration'] = song1.get('duration')
                parsed['song_1_tags'] = song1.get('tags')
                parsed['song_1_model_name'] = song1.get('model_name') or song1.get('modelName')
            
            if len(songs_data) >= 2:
                song2 = songs_data[1]
                # Try documentation format first, then fallback to other formats
                parsed['song_2_url'] = song2.get('audio_url') or song2.get('audioUrl') or song2.get('musicUrl') or song2.get('music_url') or song2.get('url')
                parsed['song_2_stream_url'] = song2.get('stream_audio_url') or song2.get('streamAudioUrl') or song2.get('stream_audio_url') or song2.get('streamUrl')
                # Additional metadata (legacy format support)
                parsed['song_2_id'] = song2.get('id')
                parsed['song_2_image_url'] = song2.get('image_url') or song2.get('imageUrl')
                parsed['song_2_duration'] = song2.get('duration')
                parsed['song_2_tags'] = song2.get('tags')
                parsed['song_2_model_name'] = song2.get('model_name') or song2.get('modelName')
            
            logger.info(f"Successfully parsed callback (simple format): {len(songs_data)} songs found")
        
        return parsed


