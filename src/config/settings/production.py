import warnings
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .base import *

if not SECRET_KEY or SECRET_KEY.startswith("your-secret"):
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required")

DEBUG = False

if not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS is required")

if "*" in ALLOWED_HOSTS:
    raise ImproperlyConfigured("Wildcard ALLOWED_HOSTS is not allowed in production")

for origin in CSRF_TRUSTED_ORIGINS:
    parsed = urlparse(origin)

    if not parsed.scheme or not parsed.netloc:
        warnings.warn(
            f"CSRF origin {origin!r} is not a valid origin "
            f"(expected scheme://host[:port])",
            stacklevel=2,
        )
        continue

    if parsed.query or parsed.fragment or parsed.path not in ("", "/"):
        warnings.warn(
            f"CSRF origin {origin!r} contains path/query/fragment "
            f"and will never match an Origin header",
            stacklevel=2,
        )
        continue

    if origin.endswith("/"):
        warnings.warn(
            f"CSRF origin {origin!r} has a trailing slash; "
            f"prefer {origin.rstrip('/')!r}",
            stacklevel=2,
        )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
