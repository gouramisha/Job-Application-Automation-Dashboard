import django_filters as filters
from django.db import transaction
from rest_framework import status as http_status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core import OwnedQuerysetMixin
from apps.jobs.models import JobStatus, JobStatusHistory
from apps.reminders.services import schedule_follow_up
from apps.resumes.models import Resume

from .models import Application
from .serializers import ApplicationSerializer, QuickApplySerializer


class ApplicationFilter(filters.FilterSet):
    outcome = filters.BaseInFilter(field_name="outcome", lookup_expr="in")
    method = filters.BaseInFilter(field_name="method", lookup_expr="in")
    job_status = filters.BaseInFilter(field_name="job__status", lookup_expr="in")
    company = filters.CharFilter(field_name="job__company_name", lookup_expr="icontains")
    submitted_after = filters.DateFilter(field_name="submitted_at", lookup_expr="date__gte")
    submitted_before = filters.DateFilter(field_name="submitted_at", lookup_expr="date__lte")

    class Meta:
        model = Application
        fields = ["outcome", "method", "job", "resume"]


class ApplicationViewSet(OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Application.objects.select_related("job", "resume")
    serializer_class = ApplicationSerializer
    filterset_class = ApplicationFilter
    search_fields = ["job__company_name", "job__job_title", "notes", "cover_letter"]
    ordering_fields = ["created_at", "submitted_at", "outcome"]
    ordering = ["-created_at"]

    @action(detail=False, methods=["post"], url_path="quick-apply")
    @transaction.atomic
    def quick_apply(self, request):
        """Log a manual application and move the job to Applied in one step."""
        serializer = QuickApplySerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        job = data["job"]
        resume = data.get("resume") or Resume.objects.filter(
            user=request.user, is_default=True
        ).first()

        application = Application.objects.create(
            user=request.user,
            job=job,
            resume=resume,
            method=Application.Method.MANUAL,
            outcome=Application.Outcome.SUBMITTED,
            cover_letter=data.get("cover_letter", ""),
            notes=data.get("notes", ""),
        )
        self._advance_job(job, application)
        return Response(
            self.get_serializer(application).data, status=http_status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"], url_path="mark-submitted")
    @transaction.atomic
    def mark_submitted(self, request, pk=None):
        """Called after the user presses Submit themselves on an
        automation-prepared application."""
        application = self.get_object()
        application.outcome = Application.Outcome.SUBMITTED
        application.error_message = ""
        application.save()
        self._advance_job(application.job, application)
        return Response(self.get_serializer(application).data)

    def _advance_job(self, job, application):
        """Push a Saved job into Applied and schedule the follow-up."""
        if job.status == JobStatus.SAVED:
            job.status = JobStatus.APPLIED
            job.save()
            JobStatusHistory.objects.create(
                job=job,
                from_status=JobStatus.SAVED,
                to_status=JobStatus.APPLIED,
                note=f"Application recorded ({application.get_method_display()})",
            )
        schedule_follow_up(application)
