import os

from django.core.validators import FileExtensionValidator
from django.db import models
from django.db.models import Q


def resume_upload_path(instance, filename):
    """Keep every user's uploads in their own directory."""
    return f"resumes/user_{instance.user_id}/{filename}"


class Resume(models.Model):
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="resumes"
    )
    name = models.CharField(
        max_length=150, help_text="A label you recognise, e.g. 'Backend - 2026'."
    )
    file = models.FileField(
        upload_to=resume_upload_path,
        validators=[FileExtensionValidator(["pdf", "doc", "docx", "rtf", "txt"])],
    )
    is_default = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    target_role = models.CharField(
        max_length=160, blank=True, help_text="Which roles this version is tuned for."
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "resumes_resume"
        ordering = ["-is_default", "-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_default=True),
                name="one_default_resume_per_user",
            ),
            models.UniqueConstraint(
                fields=["user", "name"], name="unique_resume_name_per_user"
            ),
        ]

    def __str__(self):
        return self.name

    @property
    def filename(self) -> str:
        return os.path.basename(self.file.name) if self.file else ""

    @property
    def size_bytes(self) -> int:
        try:
            return self.file.size
        except (ValueError, OSError):
            return 0

    def make_default(self):
        """Promote this resume, demoting whichever one currently holds the flag.

        Done as two writes inside the caller's transaction because the partial
        unique index above would reject two defaults existing at once.
        """
        Resume.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(
            is_default=False
        )
        if not self.is_default:
            self.is_default = True
            self.save(update_fields=["is_default", "updated_at"])
