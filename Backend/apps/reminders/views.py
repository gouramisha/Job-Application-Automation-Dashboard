from datetime import timedelta

import django_filters as filters
from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.core import OwnedQuerysetMixin

from .models import Reminder
from .serializers import ReminderSerializer


class ReminderFilter(filters.FilterSet):
    kind = filters.BaseInFilter(field_name="kind", lookup_expr="in")
    due_after = filters.DateFilter(field_name="due_date", lookup_expr="gte")
    due_before = filters.DateFilter(field_name="due_date", lookup_expr="lte")
    overdue = filters.BooleanFilter(method="filter_overdue")

    class Meta:
        model = Reminder
        fields = ["kind", "is_done", "job"]

    def filter_overdue(self, queryset, name, value):
        today = timezone.localdate()
        if value:
            return queryset.filter(is_done=False, due_date__lt=today)
        return queryset.filter(Q(is_done=True) | Q(due_date__gte=today))


class ReminderViewSet(OwnedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Reminder.objects.select_related("job")
    serializer_class = ReminderSerializer
    filterset_class = ReminderFilter
    search_fields = ["title", "notes", "job__company_name", "job__job_title"]
    ordering_fields = ["due_date", "created_at", "is_done"]
    ordering = ["is_done", "due_date"]

    @action(detail=True, methods=["post"], url_path="complete")
    def complete(self, request, pk=None):
        reminder = self.get_object()
        reminder.mark_done()
        return Response(self.get_serializer(reminder).data)

    @action(detail=True, methods=["post"], url_path="reopen")
    def reopen(self, request, pk=None):
        reminder = self.get_object()
        reminder.reopen()
        return Response(self.get_serializer(reminder).data)

    @action(detail=False, methods=["get"], url_path="upcoming")
    def upcoming(self, request):
        """Open reminders due within `days` (default 7), soonest first.
        Powers the dashboard Upcoming follow-ups panel."""
        days = int(request.query_params.get("days", 7))
        limit = int(request.query_params.get("limit", 10))
        horizon = timezone.localdate() + timedelta(days=days)
        queryset = (
            self.get_queryset()
            .filter(is_done=False, due_date__lte=horizon)
            .order_by("due_date")[:limit]
        )
        return Response(self.get_serializer(queryset, many=True).data)
