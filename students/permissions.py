from rest_framework.permissions import BasePermission


class IsVerifiedUser(BasePermission):
    """
    Allows access only to authenticated users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.verified)


class IsEligibleUser(BasePermission):
    """
    Allows access only to active & non-blocked users.
    in case we want to revoke any account at any instance of time
    """

    def has_permission(self, request, view):
        return bool(not request.user.blocked)
