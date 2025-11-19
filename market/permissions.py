from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj.owner == request.user


class IsSellerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow sellers to create products.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions require user to be authenticated and a seller
        if request.user and request.user.is_authenticated:
            return hasattr(request.user, 'profile') and request.user.profile.is_seller
        return False


class IsOrderOwner(permissions.BasePermission):
    """
    Custom permission to only allow order owners to view their orders.
    """

    def has_object_permission(self, request, view, obj):
        return obj.user == request.user


class IsMessageParticipant(permissions.BasePermission):
    """
    Custom permission to only allow message sender or receiver to view it.
    """

    def has_object_permission(self, request, view, obj):
        return obj.sender == request.user or obj.receiver == request.user
