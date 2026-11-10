"""E2E-specific setup for Playwright + Django sync ORM compatibility."""

import os

# Playwright's sync API runs an asyncio event loop in a background thread.
# Django's ORM is synchronous, and accessing it from that thread without
# this flag raises SynchronousOnlyOperation. Scoped to e2e only.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")
