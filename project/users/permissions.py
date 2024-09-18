from rest_framework import permissions


class IsUserOrCreatingAccountOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        """
        return True if user is creating a new account
        """

        if not view.detail and request.method == "GET":
            return False

        user_is_making_new_account = view.action == "create"
        if user_is_making_new_account and not request.user.is_authenticated:
            return True

        return (
            view.detail
        )  # we pass the permission to the has_object_permission function

    def has_object_permission(self, request, view, obj):
        """
        return True if user is accessing their own object
        """

        is_accessing_their_own_user_object = obj == request.user
        return is_accessing_their_own_user_object


class IsNotAuthenticated(permissions.BasePermission):
    """
    Allows access only to non authenticated users.
    """

    def has_permission(self, request, view):
        return not request.user.is_authenticated
