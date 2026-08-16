from decimal import Decimal

from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from mptt.models import MPTTModel, TreeForeignKey

from .constants import (
    AgeRatingChoices,
    FilmTypeChoices,
    FeedItemActionTypeChoices,
    UserWorkStatusChoices,
    WorkRelationTypeChoices,
)
from .validators import validate_gfk, validate_relation_type, CycleChecker


# ─── Person, Platform, Genres, Tag ────────────────────────────────────────────────


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


class GameGenre(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Tag(models.Model):
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
    tags = models.ManyToManyField(Tag, blank=True)
    external_link = models.URLField(max_length=500, blank=True, null=True)
    age_rating = models.CharField(
        choices=AgeRatingChoices.choices,
        blank=True,
    )

    relations_source = GenericRelation(
        "WorkRelation",
        related_query_name='%(app_label)s_%(class)s_source',
        content_type_field="source_content_type",
        object_id_field="source_object_id",
    )
    relations_target = GenericRelation(
        "WorkRelation",
        related_query_name='%(app_label)s_%(class)s_target',
        content_type_field="target_content_type",
        object_id_field="target_object_id",
    )
    user_works = GenericRelation(
        "UserWork",
        content_type_field="work_content_type",
        object_id_field="work_object_id",
    )
    collection_items = GenericRelation(
        "CollectionItem",
        content_type_field="work_content_type",
        object_id_field="work_object_id",
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
    episode_count = models.PositiveIntegerField(blank=True, null=True)
    film_type = models.CharField(choices=FilmTypeChoices.choices)

    class Meta(AWork.Meta):
        abstract = False
        constraints = [
            models.CheckConstraint(
                name="check_episode_count_by_type",
                condition=(
                    Q(film_type=FilmTypeChoices.MOVIE, episode_count__isnull=True) |
                    Q(film_type=FilmTypeChoices.TV_SHOW, episode_count__isnull=False)
                )
            )
        ]

    def clean(self):
        super().clean()
        if self.episode_count and self.film_type != FilmTypeChoices.TV_SHOW:
            raise ValidationError({
                'episode_count': 'Only for TV Shows'
            })
        if not self.episode_count and self.film_type == FilmTypeChoices.TV_SHOW:
            raise ValidationError({
                'episode_count': 'Must be not null for TV Shows'
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Film: {self.title}"
    

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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["source_content_type", "source_object_id", "target_content_type", "target_object_id",],
                name="unique_relation_direction",
            ),
        ]
        indexes = [
            models.Index(
                fields=["target_content_type", "target_object_id",],
                name="idx_workrelation_target",
            ),
        ]

    def __str__(self):
        return f"{self.source} → {self.relation_type} → {self.target}"

    def clean(self):
        super().clean()
        validate_gfk(self.source_content_type, self.source_object_id)
        validate_gfk(self.target_content_type, self.target_object_id)
        checker = CycleChecker(items_out=self.__get_outgoing, items_in=self.__get_incoming)
        validate_relation_type(self.source_content_type, self.target_content_type, self.relation_type)
        if self.__other_relation_exists():
            raise ValidationError("Между данными объектами уже есть связь")
        target_key = (self.target_content_type_id, self.target_object_id) # type: ignore
        source_key = (self.source_content_type_id, self.source_object_id) # type: ignore
        if checker.check(target_key, source_key):
            raise ValidationError("Цикличное создание недопустимо")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __get_outgoing(self, key):
        return WorkRelation.objects.filter(
            source_content_type_id=key[0],
            source_object_id=key[1],
        ).exclude(pk=self.pk).values_list('target_content_type_id', 'target_object_id')

    def __get_incoming(self, key):
        return WorkRelation.objects.filter(
            target_content_type_id=key[0],
            target_object_id=key[1],
            relation_type='other',
        ).exclude(pk=self.pk).values_list('source_content_type_id', 'source_object_id')

    def __other_relation_exists(self):
        return WorkRelation.objects.filter(
            source_content_type=self.target_content_type,
            source_object_id=self.target_object_id,
            target_content_type=self.source_content_type,
            target_object_id=self.source_object_id,
        ).exclude(pk=self.pk).exists()


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
        constraints = [
            models.UniqueConstraint(
                fields=["user", "work_content_type", "work_object_id"],
                name="unique_user_work",
            ),
        ]
        indexes = [
            models.Index(fields=["work_content_type", "work_object_id"]),
            models.Index(fields=["user", "order_position"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.user} — {self.work} ({self.status})"

    def clean(self):
        super().clean()
        if self.work_content_type_id and self.work_object_id:
            validate_gfk(self.work_content_type, self.work_object_id)

    def save(self, *args, **kwargs):
        self.full_clean()
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

    def clean(self):
        if not self.parent:
            return
        if self.parent.pk == self.pk:
            raise ValidationError('Объект не может быть своим родителем.')
        if not self.pk:
            return
        if self.parent.pk in self.get_descendants().values_list('pk', flat=True):
            raise ValidationError('Нельзя установить потомка в качестве родителя.')


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

    def clean(self):
        super().clean()
        validate_gfk(self.work_content_type, self.work_object_id)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


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
