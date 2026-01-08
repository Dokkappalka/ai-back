"""
Views for authentication endpoints.
"""
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from .serializers import LoginSerializer, UserSerializer


def set_refresh_token_cookie(response, refresh_token):
    """
    Helper function to set refresh token in httpOnly cookie.
    """
    cookie_settings = settings.SIMPLE_JWT.get('COOKIE_SETTINGS', {})
    
    # Refresh token cookie settings
    refresh_cookie_name = settings.SIMPLE_JWT.get('REFRESH_TOKEN_COOKIE_NAME', 'refresh_token')
    refresh_cookie_max_age = settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME').total_seconds()
    
    # Common cookie settings
    http_only = cookie_settings.get('HTTP_ONLY', True)
    secure = cookie_settings.get('SECURE', not settings.DEBUG)
    samesite = cookie_settings.get('SAMESITE', 'Lax')
    
    # Set refresh token cookie
    response.set_cookie(
        refresh_cookie_name,
        str(refresh_token),
        max_age=int(refresh_cookie_max_age),
        httponly=http_only,
        secure=secure,
        samesite=samesite,
        path=cookie_settings.get('PATH', '/'),
    )
    
    return response


def delete_refresh_token_cookie(response):
    """
    Helper function to delete refresh token cookie.
    """
    cookie_settings = settings.SIMPLE_JWT.get('COOKIE_SETTINGS', {})
    refresh_cookie_name = settings.SIMPLE_JWT.get('REFRESH_TOKEN_COOKIE_NAME', 'refresh_token')
    
    # Delete refresh token cookie
    response.delete_cookie(
        refresh_cookie_name,
        path=cookie_settings.get('PATH', '/'),
        samesite=cookie_settings.get('SAMESITE', 'Lax'),
    )
    
    return response


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Login endpoint that returns access token in JSON and stores refresh token in httpOnly cookie.
    
    POST /api/auth/login/
    Body: {
        "username": "user",
        "password": "pass"
    }
    
    Returns: {
        "access": "access_token",
        "user": {user_data}
    }
    Refresh token is stored in httpOnly cookie.
    """
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    user = serializer.validated_data['user']
    refresh = RefreshToken.for_user(user)
    
    user_serializer = UserSerializer(user)
    
    response = Response({
        'access': str(refresh.access_token),
        'user': user_serializer.data
    }, status=status.HTTP_200_OK)
    
    # Set refresh token in httpOnly cookie
    response = set_refresh_token_cookie(response, refresh)
    
    return response


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """
    Logout endpoint that deletes refresh token cookie.
    
    POST /api/auth/logout/
    Deletes refresh_token cookie. Frontend should remove access token from memory.
    """
    response = Response(
        {'message': 'Successfully logged out.'},
        status=status.HTTP_200_OK
    )
    
    # Delete refresh token cookie
    response = delete_refresh_token_cookie(response)
    
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile_view(request):
    """
    Get current user profile.
    
    GET /api/auth/me/
    Requires: Authorization header with Bearer token
    
    Returns: {
        "id": 1,
        "username": "user",
        "email": "user@example.com",
        ...
    }
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data, status=status.HTTP_200_OK)


class CookieTokenRefreshSerializer(TokenRefreshSerializer):
    """
    Custom token refresh serializer that reads refresh token from cookie.
    """
    refresh = None  # We'll get it from cookie, not from request data
    
    def validate(self, attrs):
        # Get refresh token from cookie
        refresh_cookie_name = settings.SIMPLE_JWT.get('REFRESH_TOKEN_COOKIE_NAME', 'refresh_token')
        refresh_token = self.context['request'].COOKIES.get(refresh_cookie_name)
        
        if not refresh_token:
            raise InvalidToken('No refresh token found in cookie.')
        
        attrs['refresh'] = refresh_token
        return super().validate(attrs)


class CookieTokenRefreshView(TokenRefreshView):
    """
    Custom token refresh view that reads refresh token from cookie,
    returns access token in JSON, and updates refresh token in cookie if rotated.
    """
    serializer_class = CookieTokenRefreshSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data={})
        
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])
        
        access_token = serializer.validated_data['access']
        refresh_token = serializer.validated_data.get('refresh')
        
        # Create response with access token in JSON
        response = Response({
            'access': str(access_token)
        }, status=status.HTTP_200_OK)
        
        # Update refresh token cookie if it was rotated
        if refresh_token:
            response = set_refresh_token_cookie(response, refresh_token)
        # If refresh token is not rotated, cookie remains unchanged
        
        return response

