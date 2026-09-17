"""Shared helpers used across the API apps."""
from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """Object-level guard: a row is only reachable by the user who owns it."""

    message = "You do not have access to this record."

    def has_object_permission(self, request, view, obj):
        owner = getattr(obj, "user", None)
        return owner is not None and owner == request.user


class OwnedQuerysetMixin:
    """Scopes every queryset to request.user and stamps the owner on create.

    Every model in this project is per-user, so isolation lives here rather
    than being re-implemented in each viewset.
    """

    permission_classes = [permissions.IsAuthenticated, IsOwner]

    def get_queryset(self):
        return super().get_queryset().filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
