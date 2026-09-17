from django.db.models import Count
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.models import Profile
from apps.core import OwnedQuerysetMixin

from .filters import JobFilter
from .matching import rank_jobs
from .models import Job, JobStatus, JobStatusHistory
from .serializers import (
    JobDetailSerializer,
    JobMatchSerializer,
    JobSerializer,
    JobStatusUpdateSerializer,
)


class JobViewSet(OwnedQuerysetMixin, viewsets.ModelViewSet):
    """CRUD for job opportunities, plus status transitions and matching."""

    queryset = Job.objects.all()
    serializer_class = JobSerializer
    filterset_class = JobFilter
    search_fields = ["company_name", "job_title", "location", "skills", "job_description", "notes"]
    ordering_fields = ["created_at", "updated_at", "applied_date", "company_name", "job_title", "status"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return super().get_queryset().annotate(application_count=Count("applications"))

    def get_serializer_class(self):
        if self.action == "retrieve":
            return JobDetailSerializer
        if self.action == "matches":
            return JobMatchSerializer
        return JobSerializer

    def perform_create(self, serializer):
        job = serializer.save(user=self.request.user)
        JobStatusHistory.objects.create(
            job=job, from_status="", to_status=job.status, note="Job added"
        )

    def perform_update(self, serializer):
        previous = serializer.instance.status
        job = serializer.save()
        if job.status != previous:
            JobStatusHistory.objects.create(
                job=job, from_status=previous, to_status=job.status
            )

    @action(detail=True, methods=["post"], url_path="status")
    def set_status(self, request, pk=None):
        """Dedicated transition endpoint so the Kanban/status dropdown does not
        have to PATCH the whole job."""
        job = self.get_object()
        serializer = JobStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_status = serializer.validated_data["status"]
        previous = job.status
        if new_status == previous:
            return Response(JobDetailSerializer(job, context=self.get_serializer_context()).data)
        job.status = new_status
        job.save()
        JobStatusHistory.objects.create(
            job=job,
            from_status=previous,
            to_status=new_status,
            note=serializer.validated_data.get("note", ""),
        )
        job.refresh_from_db()
        return Response(JobDetailSerializer(job, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"], url_path="favourite")
    def toggle_favourite(self, request, pk=None):
        job = self.get_object()
        job.is_favourite = not job.is_favourite
        job.save(update_fields=["is_favourite", "updated_at"])
        return Response({"id": job.id, "is_favourite": job.is_favourite})

    @action(detail=False, methods=["get"])
    def matches(self, request):
        """Rank the user's saved jobs against their profile preferences.

        Scoped to jobs not yet applied to, since the point of the view is
        deciding what to do next.
        """
        profile, _ = Profile.objects.get_or_create(user=request.user)
        candidates = self.get_queryset().filter(status=JobStatus.SAVED)
        minimum = int(request.query_params.get("min_score", 1))
        ranked = rank_jobs(candidates, profile, minimum_score=minimum)
        page = self.paginate_queryset(ranked)
        serializer = self.get_serializer(page if page is not None else ranked, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="options")
    def options_meta(self, request):
        """Choice lists for the Add Job / filter dropdowns, so the frontend
        never hardcodes them."""
        return Response(
            {
                "statuses": [{"value": v, "label": l} for v, l in Job._meta.get_field("status").choices],
                "sources": [{"value": v, "label": l} for v, l in Job._meta.get_field("source").choices],
                "companies": list(
                    self.get_queryset().values_list("company_name", flat=True).distinct().order_by("company_name")
                ),
                "locations": list(
                    self.get_queryset().exclude(location="").values_list("location", flat=True).distinct().order_by("location")
                ),
            },
            status=http_status.HTTP_200_OK,
        )
