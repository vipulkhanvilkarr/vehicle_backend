from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from .models import User, Vehicle, AuthToken
from django.contrib.auth import authenticate
from .serializers import UserSerializer, VehicleSerializer
from .serializers import VehicleTypeSerializer
from .models import VehicleType
# API endpoint to list all vehicle types
from rest_framework import generics





# Logout view for custom AuthToken
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Token '):
                token_key = auth_header.split(' ', 1)[1]
                try:
                    token = AuthToken.objects.get(key=token_key, is_active=True)
                    token.deactivate()
                except AuthToken.DoesNotExist:
                    pass  # Token is already inactive or does not exist
            # Always return success for logout
            return Response({'detail': 'Logged out successfully.'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Logout failed', 'details': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class LoginView(APIView):
    permission_classes = []

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            # Deactivate all previous tokens for this user
            AuthToken.objects.filter(user=user, is_active=True).update(is_active=False)
            token = AuthToken.create_token(user)
            return Response({
                'token': token.key,
                'user_id': user.pk,
                'username': user.username,
                'role': getattr(user, 'role', None),
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

class VehicleTypeListView(generics.ListAPIView):
    queryset = VehicleType.objects.all()
    serializer_class = VehicleTypeSerializer
    permission_classes = [IsAuthenticated]
from .permissions import RoleBasedCRUD, SuperAdminOnly

#create vehicle view
class VehicleCreateView(generics.CreateAPIView):
    """
    Create a new Vehicle.

    Permissions via RoleBasedCRUD:
    - SUPER_ADMIN: allowed
    - ADMIN: denied
    - USER: denied
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, RoleBasedCRUD]

    def create(self, request, *args, **kwargs):
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    {
                        "error": "Validation failed",
                        "details": serializer.errors,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            self.perform_create(serializer)

            return Response(
                {
                    "message": "Vehicle created successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception as e:
            # Fallback for errors
            return Response(
                {
                    "error": "Failed to create vehicle",
                    "details": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        

# vehicle list view
class VehicleListView(generics.ListAPIView):
    """
    List all vehicles.

    Permissions:
    - SUPER_ADMIN: can view
    - ADMIN: can view
    - USER: can view
    """
    queryset = Vehicle.objects.all().order_by("-id")
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, RoleBasedCRUD]

    def list(self, request, *args, **kwargs):
        try:
            return super().list(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"error": "Failed to fetch vehicles", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

#update the vehicle view
class VehicleUpdateView(generics.UpdateAPIView):
    """
    Update a vehicle.

    Permissions via RoleBasedCRUD:
    - SUPER_ADMIN: can update
    - ADMIN: can update
    - USER: cannot update
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, RoleBasedCRUD]

    def update(self, request, *args, **kwargs):
        try:
            partial = kwargs.pop("partial", False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)

            if not serializer.is_valid():
                return Response(
                    {"error": "Validation failed", "details": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            self.perform_update(serializer)

            return Response(
                {
                    "message": "Vehicle updated successfully",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"error": "Failed to update vehicle", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

#check current user details
class CurrentUserView(APIView):
    """
    Return current authenticated user (id, username, role).
    Accessible to all authenticated roles.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    

# delete vehicle view (SUPER_ADMIN only)
class VehicleDeleteView(generics.DestroyAPIView):
    """
    Delete a vehicle by ID.
    Only SUPER_ADMIN can delete vehicles.
    """
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated, SuperAdminOnly]

    def destroy(self, request, *args, **kwargs):
        try:
            self.check_permissions(request)
            response = super().destroy(request, *args, **kwargs)
            if response.status_code == status.HTTP_204_NO_CONTENT:
                return Response(
                    {"message": "Vehicle deleted successfully"},
                    status=status.HTTP_200_OK,
                )
            return response
        except Exception as e:
            return Response(
                {"error": "Failed to delete vehicle", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# create users by super admin only
class UserCreateView(generics.CreateAPIView):
    """
    Only SUPER_ADMIN can create ADMIN or USER accounts.
    (Because SuperAdminOnly allows POST only for SUPER_ADMIN)
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, SuperAdminOnly]

    def get_queryset(self):
        # Check permissions before accessing queryset
        self.check_permissions(self.request)
        return User.objects.all()

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        if data.get("role") == User.Role.SUPER_ADMIN:
            return Response(
                {"detail": "Cannot create another SUPER_ADMIN from API"},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request, *args, **kwargs)
    
# update user 
class UpdateUserView(generics.UpdateAPIView):
    """
    Update user details.
    Only SUPER_ADMIN can update users.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, SuperAdminOnly]
    def update(self, request, *args, **kwargs):
        try:
            self.check_permissions(request)
            return super().update(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"error": "Failed to update user", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        

#delete user view
class DeleteUserView(generics.DestroyAPIView):
    """
    Delete a user by ID.
    Only SUPER_ADMIN can delete users.
    """
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
        except Exception as e:
            return Response(
                {"error": "Failed to delete user", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
