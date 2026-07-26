from django.db import models
from django.db.models.signals import pre_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from . import models as vor_models
from .constants import FeedItemActionTypeChoices, UserWorkStatusChoices

# TODO: Fix userwork pre save signal
# TODO: Add signals for GenericFK

# ─── UserWork signals ────────────────────────────────────────────────────────


@receiver(pre_save, sender=vor_models.UserWork)
def userwork_pre_save(sender, instance, **kwargs):
    """Handle status changes, completions, and rating updates."""
    # Получаем старый объект из БД
    try:
        old_instance = vor_models.UserWork.objects.get(pk=instance.pk)
    except vor_models.UserWork.DoesNotExist:
        old_instance = None

    new_status = instance.status
    old_status = old_instance.status if old_instance else None

    # Если статус изменился на 'completed' и ранее не был completed
    if new_status == UserWorkStatusChoices.COMPLETED and old_status != new_status:
        instance.times_completed += 1
        instance.last_completed_date = timezone.now().date()

        # Создаём CompletionRecord
        vor_models.CompletionRecord.objects.create(user_work=instance)

    if not old_status:
        vor_models.FeedItem.objects.create(
            user=instance.user,
            user_work=instance,
            action_type=FeedItemActionTypeChoices.ADDED,
        )

    # Создаём FeedItem при изменении статуса
    if new_status != old_status:
        vor_models.FeedItem.objects.create(
            user=instance.user,
            user_work=instance,
            action_type=new_status,
        )

    # Создаём FeedItem при изменении rating
    if old_instance and instance.rating is not None and instance.rating != old_instance.rating:
        vor_models.FeedItem.objects.create(
            user=instance.user,
            user_work=instance,
            action_type=FeedItemActionTypeChoices.RATED,
        )


# ─── Cascade delete for GenericForeignKey ────────────────────────────────────


@receiver(pre_delete, sender=vor_models.WorkRelation)
def workrelation_cascade_delete(sender, instance, **kwargs):
    """Cleanup for WorkRelation GenericForeignKey."""
    pass


@receiver(pre_delete, sender=vor_models.CollectionItem)
def collectionitem_cascade_delete(sender, instance, **kwargs):
    """Cleanup for CollectionItem GenericForeignKey."""
    pass
