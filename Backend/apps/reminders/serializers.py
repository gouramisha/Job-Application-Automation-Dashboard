from rest_framework import serializers

from .models import Reminder


class ReminderSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="job.company_name", read_only=True, default=None)
    job_title = serializers.CharField(source="job.job_title", read_only=True, default=None)
    kind_display = serializers.CharField(source="get_kind_display", read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_due = serializers.IntegerField(read_only=True)

    class Meta:
        model = Reminder
        fields = [
            "id", "job", "company_name", "job_title", "application",
            "title", "kind", "kind_display", "due_date", "notes",
            "is_done", "completed_at", "is_overdue", "days_until_due",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "completed_at", "created_at", "updated_at"]

    def validate_job(self, value):
        if value and value.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Unknown job.")
        return value
