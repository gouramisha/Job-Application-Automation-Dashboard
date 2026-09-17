from django.contrib import admin

from .models import Resume


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "is_default", "target_role", "updated_at"]
    list_filter = ["is_default"]
    search_fields = ["name", "target_role"]
