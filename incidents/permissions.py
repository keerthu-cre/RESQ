from rest_framework import permissions

class IsAdminRole(permissions.BasePermission):
    """
    Allows access only to admin users.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'admin' or request.user.is_superuser or request.user.is_staff)
        )


class IsResponderRole(permissions.BasePermission):
    """
    Allows access only to responder users.
    """
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            (request.user.role == 'responder' or request.user.role == 'admin' or request.user.is_superuser)
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Allows access if the user created the incident or is an admin.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role == 'admin' or request.user.is_superuser or request.user.is_staff:
            return True
        return obj.reported_by == request.user or (
            hasattr(request.user, 'response_team') and obj.assigned_team == request.user.response_team
        )
