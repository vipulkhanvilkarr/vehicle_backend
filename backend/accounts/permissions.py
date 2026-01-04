from rest_framework.permissions import BasePermission, SAFE_METHODS


class SuperAdminOnly(BasePermission):
    """
    Only SUPER_ADMIN (or Django superuser)
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.is_super_admin() or user.is_superuser)
        )


class AdminAccess(BasePermission):
    """
    SUPER_ADMIN & ADMIN → full CRUD
    USER → read-only
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        if user.role in ("SUPER_ADMIN", "ADMIN"):
            return True

        return request.method in SAFE_METHODS
