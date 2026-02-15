from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .permissions import CanManageUsers
from .serializers import (
    UserCreateSerializer,
    UserListSerializer,
    UserPayloadSerializer,
    UserUpdateSerializer,
    CustomTokenObtainPairSerializer,
)

User = get_user_model()


class LoginView(TokenObtainPairView):
    """POST /api/v1/auth/login - Returns access, refresh, and user payload."""
    serializer_class = CustomTokenObtainPairSerializer


class RefreshView(TokenRefreshView):
    """POST /api/v1/auth/refresh - Standard token refresh."""


class MeView(APIView):
    """GET /api/v1/auth/me - Return current user payload (no tokens)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        payload = UserPayloadSerializer.from_user(request.user)
        return Response(payload.data, status=status.HTTP_200_OK)


class UserListView(APIView):
    """GET /api/v1/users - List users. POST - Create user."""
    permission_classes = [CanManageUsers]

    def get(self, request):
        users = User.objects.all().order_by('username')
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserListSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    """PATCH /api/v1/users/<id> - Update user. POST .../reset-password - Reset password."""
    permission_classes = [CanManageUsers]

    def patch(self, request, user_id):
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'roles' in data:
            from .serializers import _assign_roles
            _assign_roles(user, data['roles'])
        user.save()
        return Response(UserListSerializer(user).data, status=status.HTTP_200_OK)


class UserResetPasswordView(APIView):
    """POST /api/v1/users/<id>/reset-password - Set new password."""
    permission_classes = [CanManageUsers]

    def post(self, request, user_id):
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
        password = request.data.get('password')
        if not password or len(password) < 8:
            return Response(
                {'detail': 'Password must be at least 8 characters.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(password)
        user.save()
        return Response({'detail': 'Password updated.'}, status=status.HTTP_200_OK)
