from rest_framework.permissions import (SAFE_METHODS, BasePermission,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)


class IsAdminRole(IsAuthenticated):
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.is_admin
        )


class IsReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class RetrieveOnlyOrHasCUDPermissions(IsAuthenticatedOrReadOnly):
    def has_object_permission(self, request, view, obj):
        if view.action == 'retrieve':
            return True

        user = request.user
        return (
            user.is_admin
            or user.is_moderator
            or user == obj.author
        )


class IsMe(BasePermission):
    def has_permission(self, request, view):
        return (request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj == request.user
