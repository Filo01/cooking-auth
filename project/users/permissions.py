from rest_framework import permissions


class IsUserOrCreatingAccountOrReadOnly(permissions.BasePermission):
    """
    Object-level permission that allows users to create accounts or edit their
    own accounts.
    """

    def has_permission(self, request, view):
        if not view.detail and request.method == "GET":
            return False

        user_is_making_new_account = view.action == "create"
        if user_is_making_new_account and not request.user.is_authenticated:
            return True

        return (
            view.detail
        )  # we pass the permission to the has_object_permission function

    def has_object_permission(self, request, view, obj):
        is_accessing_their_own_user_object = obj == request.user
        return is_accessing_their_own_user_object
