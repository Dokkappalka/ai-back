"""
Authentication permissions module.

We use standard Django REST Framework permissions:
- rest_framework.permissions.IsAuthenticated - for protected endpoints
- rest_framework.permissions.AllowAny - for public endpoints (e.g., login)

Custom permissions can be added here if needed in the future.
"""
from rest_framework import permissions

# Standard DRF permissions are used throughout the application
# Custom permissions can be added here if needed

