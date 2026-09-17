from rest_framework import serializers

from apps.jobs.models import Job
from apps.resumes.models import Resume

from .models import Application


class ApplicationSerializer(serializers.ModelSerializer):
    # Denormalised for the Applications table — avoids an N+1 round trip
    # in the frontend just to render company and title.
    company_name = serializers.CharField(source="job.company_name", read_only=True)
    job_title = serializers.CharField(source="job.job_title", read_only=True)
    job_status = serializers.CharField(source="job.status", read_only=True)
    job_url = serializers.CharField(source="job.job_url", read_only=True)
    location = serializers.CharField(source="job.location", read_only=True)
    resume_label = serializers.SerializerMethodField()
    method_display = serializers.CharField(source="get_method_display", read_only=True)
    outcome_display = serializers.CharField(source="get_outcome_display", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id", "job", "company_name", "job_title", "job_status", "job_url", "location",
            "resume", "resume_label", "method", "method_display",
            "outcome", "outcome_display", "cover_letter", "answers",
            "submitted_at", "error_message", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_resume_label(self, obj):
        return obj.resume.name if obj.resume else (obj.resume_name_snapshot or None)

    def validate_job(self, value):
        if value.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Unknown job.")
        return value

    def validate_resume(self, value):
        if value and value.user_id != self.context["request"].user.id:
            raise serializers.ValidationError("Unknown resume.")
        return value


class QuickApplySerializer(serializers.Serializer):
    """Records a manual application in one call: creates the Application and
    advances the job to 'Applied'."""

    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.none())
    resume = serializers.PrimaryKeyRelatedField(
        queryset=Resume.objects.none(), required=False, allow_null=True
    )
    cover_letter = serializers.CharField(required=False, allow_blank=True)
    notes = serializers.CharField(required=False, allow_blank=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context["request"].user
        self.fields["job"].queryset = Job.objects.filter(user=user)
        self.fields["resume"].queryset = Resume.objects.filter(user=user)
