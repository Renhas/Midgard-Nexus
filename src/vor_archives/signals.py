from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone

from . import models as vor_models
from .constants import FeedItemActionTypeChoices, UserWorkStatusChoices


# ─── UserWork signals ────────────────────────────────────────────────────────


@receiver(pre_save, sender=vor_models.UserWork)
def userwork_pre_save(sender, instance, **kwargs):
    """Handle status changes, completions, and rating updates."""
    try:
        old_instance = vor_models.UserWork.objects.get(pk=instance.pk)
    except vor_models.UserWork.DoesNotExist:
        old_instance = None

    new_status = instance.status
    old_status = old_instance.status if old_instance else None

    if new_status == UserWorkStatusChoices.COMPLETED and old_status != new_status:
        instance.times_completed += 1
        instance.last_completed_date = timezone.now().date()
        vor_models.CompletionRecord.objects.create(user_work=instance)

    instance._old_status = old_status
    instance._old_rating = old_instance.rating if old_instance else None


@receiver(post_save, sender=vor_models.UserWork)
def userwork_post_save(sender, instance, created, **kwargs):
    if created:
        vor_models.FeedItem.objects.create(
            user=instance.user,
            user_work=instance,
            action_type=FeedItemActionTypeChoices.ADDED,
        )
    new_status = instance.status
    old_status = instance._old_status
    if old_status and new_status != old_status:
        vor_models.FeedItem.objects.create(
            user=instance.user,
            user_work=instance,
            action_type=new_status,
        )
    if instance.rating != instance._old_rating:
        vor_models.FeedItem.objects.create(
            user=instance.user,
            user_work=instance,
            action_type=FeedItemActionTypeChoices.RATED,
        )
