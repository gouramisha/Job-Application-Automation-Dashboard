from rest_framework import serializers

from .models import Resume


class ResumeSerializer(serializers.ModelSerializer):
    file_url = serializers.SerializerMethodField()
    filename = serializers.CharField(read_only=True)
    size_bytes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Resume
        fields = [
            "id", "name", "file", "file_url", "filename", "size_bytes",
            "is_default", "target_role", "notes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"file": {"write_only": True}}

    def get_file_url(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def validate_name(self, value):
        user = self.context["request"].user
        clash = Resume.objects.filter(user=user, name__iexact=value.strip())
        if self.instance:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError("You already have a resume with this name.")
        return value.strip()

    def validate_file(self, value):
        max_bytes = 10 * 1024 * 1024
        if value.size > max_bytes:
            raise serializers.ValidationError("Resume must be 10 MB or smaller.")
        return value
