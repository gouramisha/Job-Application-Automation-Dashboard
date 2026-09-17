from django.contrib import admin

from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ["job", "user", "method", "outcome", "submitted_at", "created_at"]
    list_filter = ["method", "outcome"]
    search_fields = ["job__company_name", "job__job_title"]
    autocomplete_fields = ["job", "resume"]
