
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.utils.translation import gettext_lazy as _
from .models import AuthToken, User

class BearerTokenAuthentication(BaseAuthentication):
    """
    Custom authentication using AuthToken model and 'Token <key>' or 'Bearer <key>' in Authorization header.
    """
    keyword = 'Token'
    alt_keyword = 'Bearer'

    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        parts = auth_header.split()
        if len(parts) != 2 or parts[0] not in (self.keyword, self.alt_keyword):
            return None
        token_key = parts[1]
        try:
            token = AuthToken.objects.get(key=token_key, is_active=True)
        except AuthToken.DoesNotExist:
            raise AuthenticationFailed(_('Invalid token.'))
        if token.is_expired():
            token.deactivate()
            raise AuthenticationFailed(_('Token expired. Token validity is 7 days from creation. Please login again.'))
        if not token.user.is_active:
            raise AuthenticationFailed(_('User inactive or deleted.'))
        # Token is valid if:
        # - Exists in DB and is_active=True
        # - Not expired (created within last 7 days)
        # - User is active
        return (token.user, token)
