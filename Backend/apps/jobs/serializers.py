from rest_framework import serializers

from .models import Job, JobStatusHistory


class JobStatusHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = JobStatusHistory
        fields = ["id", "from_status", "to_status", "note", "changed_at"]
        read_only_fields = fields


class JobSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)
    skill_list = serializers.ListField(child=serializers.CharField(), read_only=True)
    application_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Job
        fields = [
            "id", "company_name", "job_title", "location", "job_url", "salary",
            "experience_required", "skills", "skill_list", "job_description",
            "source", "source_display", "status", "status_display", "applied_date",
            "notes", "is_remote", "is_favourite", "application_count",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        # Combined with the model's partial unique index, this turns a DB
        # IntegrityError into a readable field error.
        url = attrs.get("job_url", getattr(self.instance, "job_url", ""))
        if url:
            user = self.context["request"].user
            clash = Job.objects.filter(user=user, job_url=url)
            if self.instance:
                clash = clash.exclude(pk=self.instance.pk)
            if clash.exists():
                raise serializers.ValidationError(
                    {"job_url": "You have already saved a job with this URL."}
                )
        return attrs


class JobDetailSerializer(JobSerializer):
    status_history = JobStatusHistorySerializer(many=True, read_only=True)

    class Meta(JobSerializer.Meta):
        fields = JobSerializer.Meta.fields + ["status_history"]


class JobStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Job._meta.get_field("status").choices)
    note = serializers.CharField(required=False, allow_blank=True, max_length=255)


class JobMatchSerializer(JobSerializer):
    """A job annotated with why it matched the user's stated preferences."""

    match_score = serializers.IntegerField(read_only=True)
    match_reasons = serializers.ListField(child=serializers.CharField(), read_only=True)

    class Meta(JobSerializer.Meta):
        fields = JobSerializer.Meta.fields + ["match_score", "match_reasons"]
