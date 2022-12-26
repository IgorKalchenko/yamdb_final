from rest_framework.permissions import (SAFE_METHODS, BasePermission,
                                        IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)


class IsAdminRole(IsAuthenticated):
    '''
    Checks if request user has an admin role.
    '''
    def has_permission(self, request, view):
        return (
            super().has_permission(request, view)
            and request.user.is_admin
        )


class IsReadOnly(BasePermission):
    '''
    Allows only SAFE_METHODS (GET, HEAD or OPTIONS).
    '''
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS


class RetrieveOnlyOrHasCUDPermissions(IsAuthenticatedOrReadOnly):
    '''
    Anyone has the permission to retrive an object.
    Only author, admin and moderator can modify an object.
    '''
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
    '''
    Any authenticated user has the permission to a view.
    Only author can interact with an object.
    '''
    def has_permission(self, request, view):
        return (request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj == request.user
