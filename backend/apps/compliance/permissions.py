from rest_framework.permissions import BasePermission


class HasComplianceRole(BasePermission):
    allowed_roles = ()

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if not self.allowed_roles:
            return True
        return user.groups.filter(name__in=self.allowed_roles).exists()


class IsAdminManagerAuditor(HasComplianceRole):
    allowed_roles = ('ADMIN', 'MANAGER', 'AUDITOR')


class IsAdminOrManager(HasComplianceRole):
    allowed_roles = ('ADMIN', 'MANAGER')
