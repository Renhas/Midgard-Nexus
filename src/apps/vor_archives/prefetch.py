"""Shared prefetch helpers for works and user works."""

from django.db.models import prefetch_related_objects


def prefetch_user_works(user_works):
    """Resolve ``user_work.work`` (GenericForeignKey) for a list of UserWork.

    Returns the same list back for convenient chaining.
    """
    prefetch_related_objects(user_works, "work")
    return user_works


def prefetch_work_relations(works, with_authors=False):
    """Prefetch related rows for a flat list of work instances.

    Common relations (tags, genres) are prefetched for every work;
    ``platforms`` only for games; ``authors`` only when ``with_authors``.
    Works are grouped by concrete model so that ``prefetch_related_objects``
    does not mix different model types in a single call.
    """
    by_type: dict[str, list] = {}
    for work in works:
        if work is None:
            continue
        type_key = work._meta.model_name
        by_type.setdefault(type_key, []).append(work)
    for type_key, bucket in by_type.items():
        related = ["tags", "genres"]
        if with_authors:
            related.append("authors")
        if type_key == "game":
            related.append("platforms")
        prefetch_related_objects(bucket, *related)


def prefetch_work_with_user_work(work, user_work=None):
    """Prefetch relations for a single work and optionally owned platforms.

    Returns the work's ``type_key``.
    """
    type_key = work._meta.model_name
    related = ["authors", "tags", "genres"]
    if type_key == "game":
        related.append("platforms")
    prefetch_related_objects([work], *related)
    if user_work is not None:
        prefetch_related_objects([user_work], "owned_platforms")
    return type_key
