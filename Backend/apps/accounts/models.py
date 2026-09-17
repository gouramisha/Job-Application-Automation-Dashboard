from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Manager for the email-as-username custom user."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        if extra.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, password, **extra)


class User(AbstractUser):
    """Authentication identity. Login is by email, not username."""

    username = None
    email = models.EmailField("email address", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "accounts_user"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip() or self.email


class Profile(models.Model):
    """The job-search profile. This is the data the automation module types
    into application forms, so every field here maps to a common form input."""

    class WorkAuth(models.TextChoices):
        CITIZEN = "citizen", "Citizen"
        PERMANENT_RESIDENT = "permanent_resident", "Permanent resident"
        WORK_VISA = "work_visa", "Work visa"
        STUDENT_VISA = "student_visa", "Student visa"
        NEEDS_SPONSORSHIP = "needs_sponsorship", "Needs sponsorship"
        OTHER = "other", "Other"

    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="profile"
    )

    # Contact details
    phone = models.CharField(max_length=32, blank=True)
    city = models.CharField(max_length=120, blank=True)
    state = models.CharField(max_length=120, blank=True)
    country = models.CharField(max_length=120, blank=True)
    linkedin_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)

    # Experience
    current_title = models.CharField(max_length=160, blank=True)
    current_company = models.CharField(max_length=160, blank=True)
    years_experience = models.DecimalField(
        max_digits=4, decimal_places=1, default=0,
        help_text="Total years of professional experience.",
    )
    skills = models.TextField(blank=True, help_text="Comma-separated skills.")
    summary = models.TextField(blank=True)

    # Search preferences — drive the job-matching endpoint
    desired_roles = models.TextField(
        blank=True, help_text="Comma-separated target job titles."
    )
    desired_locations = models.TextField(
        blank=True, help_text="Comma-separated target locations."
    )
    open_to_remote = models.BooleanField(default=True)
    willing_to_relocate = models.BooleanField(default=False)
    expected_salary_min = models.PositiveIntegerField(null=True, blank=True)
    expected_salary_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=8, default="USD")
    notice_period_days = models.PositiveIntegerField(default=0)

    # Answers to the recurring screening questions
    work_authorization = models.CharField(
        max_length=32, choices=WorkAuth.choices, default=WorkAuth.CITIZEN
    )
    requires_sponsorship = models.BooleanField(default=False)
    custom_answers = models.JSONField(
        default=dict, blank=True,
        help_text="Extra question -> answer pairs the form filler can reuse.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "accounts_profile"

    def __str__(self):
        return f"Profile<{self.user.email}>"

    def as_form_values(self) -> dict:
        """Flatten the profile into the key/value bag the Playwright field
        mapper consumes. Keys are the canonical field names in
        apps.automation.field_map."""
        user = self.user
        location = ", ".join(p for p in (self.city, self.state, self.country) if p)
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "full_name": user.full_name,
            "email": user.email,
            "phone": self.phone,
            "address_city": self.city,
            "address_state": self.state,
            "address_country": self.country,
            "location": location,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "portfolio_url": self.portfolio_url,
            "current_title": self.current_title,
            "current_company": self.current_company,
            "years_experience": str(self.years_experience),
            "skills": self.skills,
            "summary": self.summary,
            "expected_salary": str(self.expected_salary_max or self.expected_salary_min or ""),
            "notice_period_days": str(self.notice_period_days),
            "work_authorization": self.get_work_authorization_display(),
            "requires_sponsorship": "Yes" if self.requires_sponsorship else "No",
            "willing_to_relocate": "Yes" if self.willing_to_relocate else "No",
            **(self.custom_answers or {}),
        }


class UserSettings(models.Model):
    """Preferences surfaced on the Settings page."""

    user = models.OneToOneField(
        "accounts.User", on_delete=models.CASCADE, related_name="settings"
    )
    email_reminders = models.BooleanField(default=True)
    reminder_lead_days = models.PositiveIntegerField(
        default=1, help_text="Days before the due date a reminder becomes 'upcoming'."
    )
    default_follow_up_days = models.PositiveIntegerField(
        default=7, help_text="Auto-schedule a follow-up this many days after applying."
    )
    auto_create_follow_ups = models.BooleanField(default=True)
    theme = models.CharField(
        max_length=16,
        choices=[("light", "Light"), ("dark", "Dark"), ("system", "System")],
        default="system",
    )
    # Mirrors settings.AUTOMATION_ALLOW_AUTO_SUBMIT but scoped per user. Both
    # must be true before any automated submit is attempted.
    allow_auto_submit = models.BooleanField(
        default=False,
        help_text="Only applies to sources with an official application API.",
    )

    class Meta:
        db_table = "accounts_settings"
        verbose_name_plural = "user settings"

    def __str__(self):
        return f"Settings<{self.user.email}>"
