from django.db import models

# TODO: Remove duplicates in UserWork & FeedItemAction Types
# TODO: Localization (RU) for types

class AgeRatingChoices(models.TextChoices):
    RATING_0 = ("0+", "0+")
    RATING_6 = ("6+", "6+")
    RATING_12 = ("12+", "12+")
    RATING_16 = ("16+", "16+")
    RATING_18 = ("18+", "18+")


class WorkRelationTypeChoices(models.TextChoices):
    SEQUEL = ("sequel", "Sequel")
    SPIN_OFF = ("spin_off", "Spin-off")
    ADAPTATION = ("adaptation", "Adaptation")
    REMAKE = ("remake", "Remake")
    OTHER = ("other", "Other")


class UserWorkStatusChoices(models.TextChoices):
    PLANNING = ("planning", "Planning")
    IN_PROGRESS = ("in_progress", "In Progress")
    COMPLETED = ("completed", "Completed")
    DROPPED = ("dropped", "Dropped")


class FeedItemActionTypeChoices(models.TextChoices):
    ADDED = ("added", "Added")
    PLANNING = ("planning", "Planning")
    IN_PROGRESS = ("in_progress", "In Progress")
    COMPLETED = ("completed", "Completed")
    DROPPED = ("dropped", "Dropped")
    RATED = ("rated", "Rated")
