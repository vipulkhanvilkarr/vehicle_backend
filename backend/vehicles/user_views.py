import logging
from django.contrib.auth import authenticate, get_user_model
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from .models import User, AuthToken
from .serializers import UserSerializer
from .permissions import SuperAdminOnly
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

def create_superuser(request):
    if request.method != "POST":
        return JsonResponse({"detail": "Method not allowed"}, status=405)

    User = get_user_model()

    if User.objects.filter(is_superuser=True).exists():
        @csrf_exempt
        def create_superuser(request):
            if request.method != "POST":
                return JsonResponse({"detail": "Method not allowed"}, status=405)

            User = get_user_model()

            # Safety: if a superuser already exists, do NOT create another
            if User.objects.filter(is_superuser=True).exists():
                return JsonResponse({"detail": "Superuser already exists"}, status=400)

            expected_secret = getattr(settings, "SETUP_SECRET", None)

            try:
                data = json.loads(request.body.decode() if request.body else "{}")
            except Exception:
                return JsonResponse({"detail": "Invalid JSON"}, status=400)

            username = data.get("username")
            email = data.get("email") or username
            password = data.get("password")
            secret = data.get("secret")

            if expected_secret and secret != expected_secret:
                return JsonResponse({"detail": "Forbidden"}, status=403)

            if not email or not password:
                return JsonResponse({"detail": "Email and password are required"}, status=400)

            user = User.objects.create_superuser(
                username=email,
                email=email,
                password=password,
            )

            # Set role to SUPER_ADMIN if your model has Role
            if hasattr(user, "role") and hasattr(User, "Role"):
                user.role = User.Role.SUPER_ADMIN
                user.save(update_fields=["role"])

            return JsonResponse({"detail": "Superuser created successfully"}, status=201)
    permission_classes = [IsAuthenticated, SuperAdminOnly]

    def get_queryset(self):
        self.check_permissions(self.request)
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if data.get("role") == User.Role.SUPER_ADMIN:
            return Response(
                {"detail": "Cannot create another SUPER_ADMIN from API"},
                status=status.HTTP_403_FORBIDDEN,
            )
        email = data.get("email")
        password = data.get("password")
        if not email or not password:
            return Response({"detail": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)
        data["username"] = email  # Use email as username
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

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
                return Response({"message": "User deleted successfully"}, status=status.HTTP_200_OK)
            return response
        except Exception as exc:
            logger.exception("Failed to delete user: %s", exc)
            return Response(
                {"error": "Failed to delete user", "details": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        if not username or not password:
            return Response({"message": "Username and password required."}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(username=username, password=password)
        if user is not None:
            AuthToken.objects.filter(user=user, is_active=True).update(is_active=False)
            token = AuthToken.create_token(user)
            token_key = getattr(token, "key", None) or str(token)
            return Response(
                {
                    "token": token_key,
                    "message": "Login successful."
                },
                status=status.HTTP_200_OK,
            )
        return Response({"message": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

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
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)

class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
