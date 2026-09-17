from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.core import OwnedQuerysetMixin

from .models import Resume
from .serializers import ResumeSerializer


class ResumeViewSet(OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Resume.objects.all()
    serializer_class = ResumeSerializer
    parser_classes = [MultiPartParser, FormParser]
    search_fields = ["name", "target_role", "notes"]
    ordering_fields = ["created_at", "updated_at", "name"]

    @transaction.atomic
    def perform_create(self, serializer):
        wants_default = serializer.validated_data.get("is_default", False)
        is_first = not Resume.objects.filter(user=self.request.user).exists()
        resume = serializer.save(user=self.request.user, is_default=False)
        # The first resume becomes the default automatically — otherwise the
        # user uploads one file and still has nothing selected for automation.
        if wants_default or is_first:
            resume.make_default()

    @transaction.atomic
    def perform_update(self, serializer):
        wants_default = serializer.validated_data.pop("is_default", None)
        resume = serializer.save()
        if wants_default:
            resume.make_default()

    def perform_destroy(self, instance):
        was_default = instance.is_default
        file_ref = instance.file
        instance.delete()
        if file_ref:
            file_ref.delete(save=False)
        if was_default:
            # Keep exactly one default alive so job applications always have
            # a resume to fall back on.
            replacement = Resume.objects.filter(user=self.request.user).first()
            if replacement:
                replacement.make_default()

    @action(detail=True, methods=["post"], url_path="set-default")
    @transaction.atomic
    def set_default(self, request, pk=None):
        resume = self.get_object()
        resume.make_default()
        return Response(self.get_serializer(resume).data)
