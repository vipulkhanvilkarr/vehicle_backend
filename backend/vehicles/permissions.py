from rest_framework.permissions import BasePermission, SAFE_METHODS


class SuperAdminOnly(BasePermission):
    """
    Only SUPER_ADMIN can access the view.
    (Useful for user creation, dangerous admin actions, etc.)
    """

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_super_admin())


class RoleBasedCRUD(BasePermission):
    """
    Global rule used for resources like Vehicle:

    - SUPER_ADMIN: full CRUD (GET/POST/PUT/PATCH/DELETE)
    - ADMIN: can view (GET) + update (PUT/PATCH)
    - USER: can only view (GET)

    Use this in any ViewSet where you want this exact access pattern.
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            return False

        # SUPER_ADMIN always allowed
        if user.is_super_admin():
            return True

        # Safe methods: GET, HEAD, OPTIONS -> all authenticated roles
        if request.method in SAFE_METHODS:
            return True

        # Non-safe methods: POST, PUT, PATCH, DELETE

        # ADMIN can edit (PUT/PATCH)
        if request.method in ("PUT", "PATCH"):
            return user.is_admin()

        # USER and ADMIN cannot POST or DELETE
        if request.method in ("POST", "DELETE"):
            return False

        return False
