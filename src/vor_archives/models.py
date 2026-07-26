from decimal import Decimal

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey

from .constants import (
    AgeRatingChoices,
    FeedItemActionTypeChoices,
    UserWorkStatusChoices,
    WorkRelationTypeChoices,
)

# TODO: ID check for GenericFK

# ─── Person, Platform, Genres ────────────────────────────────────────────────


class Person(models.Model):
    name = models.CharField(max_length=255, unique=True)
    bio = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Platform(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class BookGenre(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class FilmGenre(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class SeriesGenre(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class GameGenre(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


# ─── Abstract base ───────────────────────────────────────────────────────────


class AWork(models.Model):
    title = models.CharField(max_length=255)
    release_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    cover = models.ImageField(upload_to="covers/", blank=True, null=True)
    authors = models.ManyToManyField(Person, blank=True)
    external_link = models.URLField(max_length=500, blank=True, null=True)
    age_rating = models.CharField(
        max_length=3,
        choices=AgeRatingChoices.choices,
        blank=True,
        null=True,
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.title


# ─── Concrete works ──────────────────────────────────────────────────────────


class Book(AWork):
    pages = models.PositiveIntegerField()
    genres = models.ManyToManyField(BookGenre, blank=True)

    def __str__(self):
        return f"Book: {self.title}"


class Film(AWork):
    duration_minutes = models.PositiveIntegerField()
    genres = models.ManyToManyField(FilmGenre, blank=True)

    def __str__(self):
        return f"Film: {self.title}"


class Series(AWork):
    total_episodes = models.PositiveIntegerField()
    episode_duration_minutes = models.PositiveIntegerField()
    genres = models.ManyToManyField(SeriesGenre, blank=True)

    def __str__(self):
        return f"Series: {self.title}"


class Game(AWork):
    platforms = models.ManyToManyField(Platform, blank=True)
    genres = models.ManyToManyField(GameGenre, blank=True)

    def __str__(self):
        return f"Game: {self.title}"


# ─── WorkRelation ────────────────────────────────────────────────────────────


class WorkRelation(models.Model):
    source_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="source_relations",
    )
    source_object_id = models.PositiveIntegerField()
    source = GenericForeignKey("source_content_type", "source_object_id")

    target_content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        related_name="target_relations",
    )
    target_object_id = models.PositiveIntegerField()
    target = GenericForeignKey("target_content_type", "target_object_id")

    relation_type = models.CharField(
        max_length=20,
        choices=WorkRelationTypeChoices.choices,
    )

    def __str__(self):
        return f"{self.source} → {self.relation_type} → {self.target}"


# ─── UserWork ────────────────────────────────────────────────────────────────


class UserWork(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="user_works")
    work_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    work_object_id = models.PositiveIntegerField()
    work = GenericForeignKey("work_content_type", "work_object_id")

    status = models.CharField(
        max_length=20,
        choices=UserWorkStatusChoices.choices,
        default=UserWorkStatusChoices.PLANNING,
    )
    rating = models.PositiveSmallIntegerField(
        blank=True,
        null=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
    )
    order_position = models.IntegerField(default=0)
    is_hidden = models.BooleanField(default=False)
    progress = models.DecimalField(
        max_digits=7,
        decimal_places=1,
        default=Decimal("0"),
    )
    times_completed = models.IntegerField(default=0)
    date_added = models.DateTimeField(auto_now_add=True)
    last_completed_date = models.DateField(null=True, blank=True)
    owned_platforms = models.ManyToManyField(Platform, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["work_content_type", "work_object_id"]),
            models.Index(fields=["user", "order_position"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.user} — {self.work} ({self.status})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)


# ─── CompletionRecord ────────────────────────────────────────────────────────


class CompletionRecord(models.Model):
    user_work = models.ForeignKey(
        UserWork,
        on_delete=models.CASCADE,
        related_name="completions",
    )
    date = models.DateTimeField(auto_now_add=True)
    comment = models.TextField(blank=True)
    platform = models.ForeignKey(
        Platform,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    class Meta:
        indexes = [
            models.Index(fields=["user_work", "date"]),
        ]

    def __str__(self):
        return f"Completion: {self.user_work} at {self.date}"


# ─── Collection (tree) ───────────────────────────────────────────────────────


class Collection(MPTTModel):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="collections")
    name = models.CharField(max_length=255)
    parent = TreeForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )

    class Meta(MPTTModel.Meta):
        abstract = False

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return f"Collection: {self.name} ({self.user})"


# ─── CollectionItem ──────────────────────────────────────────────────────────


class CollectionItem(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="items")
    work_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    work_object_id = models.PositiveIntegerField()
    work = GenericForeignKey("work_content_type", "work_object_id")
    order = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=["collection", "order"]),
        ]

    def __str__(self):
        return f"Item in {self.collection}: {self.work}"


# ─── FeedItem ────────────────────────────────────────────────────────────────


class FeedItem(models.Model):
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="feed_items")
    user_work = models.ForeignKey(
        UserWork,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="feed_items",
    )
    action_type = models.CharField(
        max_length=20,
        choices=FeedItemActionTypeChoices.choices,
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "timestamp"]),
        ]

    def __str__(self):
        return f"{self.user} — {self.action_type} at {self.timestamp}"
