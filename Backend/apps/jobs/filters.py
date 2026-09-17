import django_filters as filters

from .models import Job


class JobFilter(filters.FilterSet):
    """Backs the Jobs page filter bar."""

    status = filters.BaseInFilter(field_name="status", lookup_expr="in")
    source = filters.BaseInFilter(field_name="source", lookup_expr="in")
    company_name = filters.CharFilter(lookup_expr="icontains")
    location = filters.CharFilter(lookup_expr="icontains")
    skills = filters.CharFilter(field_name="skills", lookup_expr="icontains")
    applied_after = filters.DateFilter(field_name="applied_date", lookup_expr="gte")
    applied_before = filters.DateFilter(field_name="applied_date", lookup_expr="lte")
    created_after = filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    created_before = filters.DateFilter(field_name="created_at", lookup_expr="date__lte")

    class Meta:
        model = Job
        fields = ["status", "source", "is_remote", "is_favourite"]
