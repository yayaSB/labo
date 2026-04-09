from rest_framework.permissions import BasePermission


class HasAPIRole(BasePermission):
    """
    Permission DRF basee sur les roles metier normalises via user.role_api.
    La vue doit definir `allowed_roles = ["etudiant", ...]`.
    """

    def has_permission(self, request, view):
        allowed_roles = getattr(view, "allowed_roles", [])
        if not request.user or not request.user.is_authenticated:
            return False
        if not allowed_roles:
            return True
        return request.user.role_api in allowed_roles

