from rest_framework import serializers

from apps.jobs.models import Job
from apps.resumes.models import Resume

from .models import AutomationLog, AutomationRun, SupportedSite


class SupportedSiteSerializer(serializers.ModelSerializer):
    auto_submit_eligible = serializers.BooleanField(read_only=True)

    class Meta:
        model = SupportedSite
        fields = [
            "id", "name", "domain", "is_enabled", "supports_official_api",
            "auto_submit_eligible", "api_docs_url", "notes",
        ]


class AutomationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AutomationLog
        fields = ["id", "level", "message", "detail", "created_at"]
        read_only_fields = fields


class AutomationRunSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="job.company_name", read_only=True)
    job_title = serializers.CharField(source="job.job_title", read_only=True)
    resume_name = serializers.CharField(source="resume.name", read_only=True, default=None)
    site_name = serializers.CharField(source="site.name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)
    is_terminal = serializers.BooleanField(read_only=True)
    screenshot_url = serializers.SerializerMethodField()
    filled_count = serializers.SerializerMethodField()

    class Meta:
        model = AutomationRun
        fields = [
            "id", "job", "company_name", "job_title", "application",
            "resume", "resume_name", "site", "site_name", "target_url",
            "status", "status_display", "fields_filled", "filled_count",
            "fields_skipped", "unanswered_questions", "resume_uploaded",
            "screenshot_url", "submit_attempted", "stop_reason", "error_message",
            "duration_seconds", "is_terminal", "started_at", "finished_at", "created_at",
        ]
        read_only_fields = fields

    def get_screenshot_url(self, obj):
        if not obj.screenshot:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.screenshot.url) if request else obj.screenshot.url

    def get_filled_count(self, obj):
        return len(obj.fields_filled or {})


class AutomationRunDetailSerializer(AutomationRunSerializer):
    logs = AutomationLogSerializer(many=True, read_only=True)

    class Meta(AutomationRunSerializer.Meta):
        fields = AutomationRunSerializer.Meta.fields + ["logs"]
        read_only_fields = fields


class StartRunSerializer(serializers.Serializer):
    job = serializers.PrimaryKeyRelatedField(queryset=Job.objects.none())
    resume = serializers.PrimaryKeyRelatedField(
        queryset=Resume.objects.none(), required=False, allow_null=True
    )
    target_url = serializers.URLField(
        required=False, allow_blank=True,
        help_text="Defaults to the job's saved application URL.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        user = self.context["request"].user
        self.fields["job"].queryset = Job.objects.filter(user=user)
        self.fields["resume"].queryset = Resume.objects.filter(user=user)

    def validate(self, attrs):
        url = attrs.get("target_url") or attrs["job"].job_url
        if not url:
            raise serializers.ValidationError(
                {"target_url": "This job has no application URL. Add one first."}
            )
        attrs["target_url"] = url
        return attrs
