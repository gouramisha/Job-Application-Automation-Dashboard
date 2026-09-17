from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.core import OwnedQuerysetMixin

from .models import AutomationRun, SupportedSite
from .serializers import (
    AutomationRunDetailSerializer,
    AutomationRunSerializer,
    StartRunSerializer,
    SupportedSiteSerializer,
)
from .services import may_auto_submit, queue_run, resolve_site


class AutomationRunViewSet(
    OwnedQuerysetMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Runs are created through `start`, never by a plain POST, because the
    allowlist and submit-policy checks live in the service layer."""

    queryset = AutomationRun.objects.select_related("job", "resume", "site")
    serializer_class = AutomationRunSerializer
    filterset_fields = ["status", "job"]
    ordering_fields = ["created_at", "finished_at"]
    ordering = ["-created_at"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AutomationRunDetailSerializer
        return AutomationRunSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == "retrieve":
            return queryset.prefetch_related("logs")
        return queryset

    @action(detail=False, methods=["post"])
    def start(self, request):
        """Queue a form-fill run. The worker process picks it up; the client
        polls this run's detail endpoint for progress."""
        serializer = StartRunSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            run = queue_run(
                user=request.user,
                job=data["job"],
                resume=data.get("resume"),
                target_url=data["target_url"],
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            AutomationRunDetailSerializer(run, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        run = self.get_object()
        if run.is_terminal:
            return Response(
                {"detail": "This run has already finished."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        run.mark_finished(AutomationRun.Status.CANCELLED, stop_reason="Cancelled by you.")
        return Response(self.get_serializer(run).data)

    @action(detail=False, methods=["get"], url_path="preflight")
    def preflight(self, request):
        """Tell the UI, before anything launches, what will happen to a URL:
        is the host supported, and will the run stop before Submit?"""
        url = request.query_params.get("url", "")
        if not url:
            return Response({"detail": "Pass a ?url= to check."}, status=status.HTTP_400_BAD_REQUEST)

        site = resolve_site(url)
        allowed, reason = may_auto_submit(request.user, site)
        return Response(
            {
                "url": url,
                "supported": bool(site and site.is_enabled),
                "site": SupportedSiteSerializer(site).data if site else None,
                "will_auto_submit": allowed,
                "submit_policy": reason or "This site supports official API submission.",
            }
        )


class SupportedSiteViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """Read-only: the allowlist is curated in the admin after a human has
    checked each site's terms of service."""

    queryset = SupportedSite.objects.filter(is_enabled=True)
    serializer_class = SupportedSiteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
