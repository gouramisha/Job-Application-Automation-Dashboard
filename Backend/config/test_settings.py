"""Settings for the test suite.

Only two things differ from development, and both are about speed: tests run
against SQLite in memory, and password hashing drops to MD5. Real PBKDF2
hashing dominates the runtime of any suite that creates users, and the tests
care about authentication behaviour, not about the hash itself.

    python manage.py test --settings=config.test_settings
"""
from .settings import *  # noqa: F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Uploads during tests land in a throwaway directory rather than in media/.
import tempfile  # noqa: E402

MEDIA_ROOT = tempfile.mkdtemp(prefix="jobtrack-test-media-")

# The filler must never open a window during a test run.
AUTOMATION_HEADLESS = True
AUTOMATION_ALLOW_AUTO_SUBMIT = False

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"null": {"class": "logging.NullHandler"}},
    "root": {"handlers": ["null"], "level": "CRITICAL"},
}
