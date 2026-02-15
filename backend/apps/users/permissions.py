"""
RBAC permission classes using Django Groups.
Canonical roles: ADMIN, MANAGER, AUDITOR, DATA_ENTRY, VIEWER
"""

from rest_framework.permissions import BasePermission

CANONICAL_ROLES = ('ADMIN', 'MANAGER', 'AUDITOR', 'DATA_ENTRY', 'VIEWER')


def user_has_role(user, role_name: str) -> bool:
    """Check if user has the given role (group name)."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name=role_name).exists()


def user_has_any_role(user, role_names: list[str]) -> bool:
    """Check if user has any of the given roles."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return user.groups.filter(name__in=role_names).exists()


class IsAdmin(BasePermission):
    """ADMIN role or superuser."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return user.is_superuser or user_has_role(user, 'ADMIN')


class CanManageUsers(BasePermission):
    """Same as IsAdmin - user management is ADMIN-only."""

    def has_permission(self, request, view):
        return IsAdmin().has_permission(request, view)


class CanWriteEvidence(BasePermission):
    """ADMIN or MANAGER or DATA_ENTRY can create/upload evidence."""

    def has_permission(self, request, view):
        return user_has_any_role(request.user, ['ADMIN', 'MANAGER', 'DATA_ENTRY'])


class CanVerifyControls(BasePermission):
    """ADMIN or MANAGER can verify/reject controls."""

    def has_permission(self, request, view):
        return user_has_any_role(request.user, ['ADMIN', 'MANAGER'])


class CanExport(BasePermission):
    """ADMIN or MANAGER or AUDITOR can export."""

    def has_permission(self, request, view):
        return user_has_any_role(request.user, ['ADMIN', 'MANAGER', 'AUDITOR'])


class CanViewAudit(BasePermission):
    """ADMIN or MANAGER or AUDITOR can view audit events."""

    def has_permission(self, request, view):
        return user_has_any_role(request.user, ['ADMIN', 'MANAGER', 'AUDITOR'])


class CanReadControls(BasePermission):
    """Any authenticated user (all roles) can read controls."""

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        return True
