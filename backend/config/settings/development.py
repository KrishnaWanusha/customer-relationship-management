from .base import *  # noqa: F403

DEBUG = os.getenv("DJANGO_DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1,[::1],testserver",
    ).split(",")
    if host.strip()
]

CORS_ALLOW_ALL_ORIGINS = os.getenv("CORS_ALLOW_ALL_ORIGINS", "False").lower() in (
    "true",
    "1",
    "yes",
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
