from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from mptt.admin import DraggableMPTTAdmin

from . import models

# TODO: Fix ContentTypes list (to many) for select in admin panel

# ─── Generic inlines ─────────────────────────────────────────────────────────


class WorkRelationInline(GenericTabularInline):
    model = models.WorkRelation
    fk_name = "source"
    ct_field = "source_content_type"
    ct_fk_field = "source_object_id"
    extra = 0


class CollectionItemInline(GenericTabularInline):
    model = models.CollectionItem
    ct_field = "work_content_type"
    ct_fk_field = "work_object_id"
    extra = 0


# ─── Person & Platform ───────────────────────────────────────────────────────


@admin.register(models.Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.Platform)
class PlatformAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# ─── Genres ──────────────────────────────────────────────────────────────────


@admin.register(models.BookGenre)
class BookGenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.FilmGenre)
class FilmGenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.SeriesGenre)
class SeriesGenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(models.GameGenre)
class GameGenreAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


# ─── Works ───────────────────────────────────────────────────────────────────


class AWorkAdmin(admin.ModelAdmin):
    list_display = ("title", "release_date", "age_rating")
    search_fields = ("title",)
    list_filter = ("age_rating", "release_date")
    filter_horizontal = ("authors",)
    inlines = [WorkRelationInline]


@admin.register(models.Book)
class BookAdmin(AWorkAdmin):
    list_display = ("title", "pages", "release_date", "age_rating")


@admin.register(models.Film)
class FilmAdmin(AWorkAdmin):
    list_display = ("title", "duration_minutes", "release_date", "age_rating")


@admin.register(models.Series)
class SeriesAdmin(AWorkAdmin):
    list_display = ("title", "total_episodes", "episode_duration_minutes", "release_date", "age_rating")


@admin.register(models.Game)
class GameAdmin(AWorkAdmin):
    list_display = ("title", "release_date", "age_rating")
    filter_horizontal = ("authors", "platforms")


# ─── WorkRelation ────────────────────────────────────────────────────────────


@admin.register(models.WorkRelation)
class WorkRelationAdmin(admin.ModelAdmin):
    list_display = ("source", "target", "relation_type")
    list_filter = ("relation_type",)


# ─── UserWork ────────────────────────────────────────────────────────────────


@admin.register(models.UserWork)
class UserWorkAdmin(admin.ModelAdmin):
    list_display = ("user", "work", "status", "rating", "progress", "date_added")
    list_filter = ("status", "rating")
    search_fields = ("user__username",)
    date_hierarchy = "date_added"


# ─── CompletionRecord ────────────────────────────────────────────────────────


@admin.register(models.CompletionRecord)
class CompletionRecordAdmin(admin.ModelAdmin):
    list_display = ("user_work", "date", "platform")
    list_filter = ("date", "platform")
    date_hierarchy = "date"


# ─── Collection ──────────────────────────────────────────────────────────────


@admin.register(models.Collection)
class CollectionAdmin(DraggableMPTTAdmin):
    mptt_indent_field = "name"
    list_display = ("name", "user", "parent")
    list_display_links = ("name",)
    list_filter = ("user",)


# ─── CollectionItem ──────────────────────────────────────────────────────────


@admin.register(models.CollectionItem)
class CollectionItemAdmin(admin.ModelAdmin):
    list_display = ("collection", "work", "order")
    list_filter = ("collection",)


# ─── FeedItem ────────────────────────────────────────────────────────────────


@admin.register(models.FeedItem)
class FeedItemAdmin(admin.ModelAdmin):
    list_display = ("user", "action_type", "timestamp")
    list_filter = ("action_type", "timestamp")
    search_fields = ("user__username",)
    date_hierarchy = "timestamp"
