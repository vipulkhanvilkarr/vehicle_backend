from rest_framework.permissions import BasePermission
from garages.models import GarageUser


class IsGarageMember(BasePermission):
    """Allow access only to users who are active members of a garage."""

    def has_permission(self, request, view):
        user = request.user
        if not getattr(user, "is_authenticated", False):
            return False
        return GarageUser.objects.filter(user=user, is_active=True).exists()