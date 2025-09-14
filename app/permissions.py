from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework import status

class MustChangePasswordPermission(BasePermission):
    message = "You must update your password before accessing other resources."

    def has_permission(self, request, view):
        if request.user.is_authenticated and getattr(request.user, "must_change_password", False):
            # Only allow /me/ (PATCH to update password)
            if request.path.startswith("/api/me/") and request.method in ["PATCH", "GET"]:
                return True
            return False
        return True
