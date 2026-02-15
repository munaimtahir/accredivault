from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

CANONICAL_ROLES = ('ADMIN', 'MANAGER', 'AUDITOR', 'DATA_ENTRY', 'VIEWER')


def _get_user_roles(user) -> list[str]:
    """Return list of group names the user belongs to (canonical roles only)."""
    if not user or not user.is_authenticated:
        return []
    names = list(user.groups.filter(name__in=CANONICAL_ROLES).values_list('name', flat=True))
    return names


class UserPayloadSerializer(serializers.Serializer):
    """Minimal user payload for auth responses."""

    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    roles = serializers.ListField(child=serializers.CharField(), read_only=True)
    is_superuser = serializers.BooleanField(read_only=True)

    @classmethod
    def from_user(cls, user):
        return cls({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name or '',
            'last_name': user.last_name or '',
            'roles': _get_user_roles(user),
            'is_superuser': user.is_superuser,
        })


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Extended JWT serializer that includes user payload."""

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserPayloadSerializer.from_user(self.user).data
        return data


class UserListSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'is_active', 'roles']

    def get_roles(self, obj):
        return _get_user_roles(obj)


class UserCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(required=False, allow_blank=True, default='')
    last_name = serializers.CharField(required=False, allow_blank=True, default='')
    roles = serializers.ListField(child=serializers.CharField(), required=False, default=list)

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('Username already exists.')
        return value

    def validate_roles(self, value):
        invalid = [r for r in value if r not in CANONICAL_ROLES]
        if invalid:
            raise serializers.ValidationError(f'Invalid roles: {invalid}. Allowed: {CANONICAL_ROLES}')
        return value

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError('Password must be at least 8 characters.')
        return value

    def create(self, validated_data):
        roles = validated_data.pop('roles', [])
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
        )
        _assign_roles(user, roles)
        return user


class UserUpdateSerializer(serializers.Serializer):
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    is_active = serializers.BooleanField(required=False)
    roles = serializers.ListField(child=serializers.CharField(), required=False)

    def validate_roles(self, value):
        if value is None:
            return value
        invalid = [r for r in value if r not in CANONICAL_ROLES]
        if invalid:
            raise serializers.ValidationError(f'Invalid roles: {invalid}. Allowed: {CANONICAL_ROLES}')
        return value


def _assign_roles(user, role_names: list[str]) -> None:
    """Replace user's groups with canonical role groups (by name)."""
    from django.contrib.auth.models import Group
    groups = Group.objects.filter(name__in=role_names)
    user.groups.set(groups)
