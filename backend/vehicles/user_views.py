import json
import logging

from django.contrib.auth import authenticate, get_user_model
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User, AuthToken
from .serializers import UserSerializer
from .permissions import SuperAdminOnly

logger = logging.getLogger(__name__)


 
# One-time Superuser Creator
 

# Startup superuser creation (runs when server starts)
def create_default_superuser():
    UserModel = get_user_model()
    email = "vipulkhanvilkar02@gmail.com"
    password = "Vipul@2308"
    if not UserModel.objects.filter(email=email, is_superuser=True).exists():
        user = UserModel.objects.create_superuser(
            username=email,
            email=email,
            password=password,
        )
        if hasattr(user, "Role"):
            user.role = user.Role.SUPER_ADMIN
            user.save(update_fields=["role"])


 
# User Views

class UserListView(generics.ListAPIView):
    queryset = User.objects.all().order_by("-id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, SuperAdminOnly]


class UserCreateView(generics.CreateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, SuperAdminOnly]

    def get_queryset(self):
        self.check_permissions(self.request)
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()

        # Prevent creating another SUPER_ADMIN via API
        if data.get("role") == User.Role.SUPER_ADMIN:
            return Response(
                {"detail": "Cannot create another SUPER_ADMIN from API"},
                status=status.HTTP_403_FORBIDDEN,
            )

        username = data.get("username")
        password = data.get("password")
        role = data.get("role", User.Role.USER)

        if not username or not password:
            return Response(
                {"detail": "Username and password are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check  same username and role already exists
        if User.objects.filter(username=username, role=role).exists():
            return Response(
                {"detail": f"User with username '{username}' and role '{role}' already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data["username"] = username

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers,
        )


class UpdateUserView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, SuperAdminOnly]

    def update(self, request, *args, **kwargs):
        try:
            self.check_permissions(request)
            return super().update(request, *args, **kwargs)
        except Exception as exc:
            logger.exception("Failed to update user: %s", exc)
            return Response(
                {"error": "Failed to update user", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class DeleteUserView(generics.DestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, SuperAdminOnly]

    def destroy(self, request, *args, **kwargs):
        try:
            self.check_permissions(request)
            response = super().destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return Response(
                    {"message": "User deleted successfully"},
                    status=status.HTTP_200_OK,
                )
            return response
        except Exception as exc:
            logger.exception("Failed to delete user: %s", exc)
            return Response(
                {"error": "Failed to delete user", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


 
# Auth Views
 
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response(
                {"message": "Username and password required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = authenticate(username=username, password=password)

        if user is not None:
            # Deactivate any existing active tokens
            AuthToken.objects.filter(user=user, is_active=True).update(is_active=False)
            token = AuthToken.create_token(user)
            token_key = getattr(token, "key", None) or str(token)

            return Response(
                {
                    "token": token_key,
                    "message": "Login successful.",
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {"message": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )


class LogoutView(APIView):
    permission_classes = []

    def post(self, request):
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Token "):
            token_key = auth_header.split(" ", 1)[1]
            try:
                token = AuthToken.objects.get(key=token_key, is_active=True)
                token.deactivate()
            except AuthToken.DoesNotExist:
                pass

        # Always return success, even if token is missing or invalid
        return Response(
            {"detail": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
