from django.contrib import admin

from .models import Job, JobStatusHistory


class StatusHistoryInline(admin.TabularInline):
    model = JobStatusHistory
    extra = 0
    readonly_fields = ["from_status", "to_status", "note", "changed_at"]


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ["job_title", "company_name", "user", "status", "applied_date", "created_at"]
    list_filter = ["status", "source", "is_remote"]
    search_fields = ["job_title", "company_name", "location", "skills"]
    inlines = [StatusHistoryInline]
