from django.contrib import admin

from .models import AutomationLog, AutomationRun, SupportedSite


@admin.register(SupportedSite)
class SupportedSiteAdmin(admin.ModelAdmin):
    list_display = ["name", "domain", "is_enabled", "supports_official_api"]
    list_filter = ["is_enabled", "supports_official_api"]
    search_fields = ["name", "domain"]


class AutomationLogInline(admin.TabularInline):
    model = AutomationLog
    extra = 0
    readonly_fields = ["level", "message", "detail", "created_at"]


@admin.register(AutomationRun)
class AutomationRunAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "job", "status", "resume_uploaded", "created_at"]
    list_filter = ["status", "resume_uploaded", "submit_attempted"]
    search_fields = ["target_url", "job__company_name"]
    inlines = [AutomationLogInline]
