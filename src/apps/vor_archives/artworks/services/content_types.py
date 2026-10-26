"""ContentType lookups for work models and instances."""

from django.contrib.contenttypes.models import ContentType

from .constants import WORK_MODELS


def ct_for(work):
    """Return the ContentType for a work instance."""
    return ContentType.objects.get_for_model(work)


def ct_for_type(type_key):
    """Return the ContentType for a work model, looked up by type key.

    Raises KeyError for unknown type_key, matching WORK_MODELS lookup.
    """
    return ContentType.objects.get_for_model(WORK_MODELS[type_key])
