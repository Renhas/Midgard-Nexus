from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal, Tuple

WorkKind = Literal["book", "film", "game"]
FilmType = Literal["movie", "tv_show"]


@dataclass(frozen=True)
class AttrSpec:
    name: str
    description: str = ""


@dataclass(frozen=True)
class PersonSpec:
    name: str
    bio: str = ""


@dataclass(frozen=True)
class PlatformSpec:
    name: str


@dataclass(frozen=True)
class _BaseWorkSpec:
    title: str
    release_date: date | None
    description: str
    age_rating: str
    authors: Tuple[str, ...]
    tags: Tuple[str, ...]
    external_link: str | None = None
    is_fictional: bool = False
    cover_filename: str | None = None  # if set + present in covers/ -> used as-is


@dataclass(frozen=True)
class BookSpec(_BaseWorkSpec):
    genres: Tuple[str, ...] = ()
    pages: int = 0


@dataclass(frozen=True)
class FilmSpec(_BaseWorkSpec):
    genres: Tuple[str, ...] = ()
    duration_minutes: int = 0
    film_type: FilmType = "movie"
    episode_count: int | None = None


@dataclass(frozen=True)
class GameSpec(_BaseWorkSpec):
    genres: Tuple[str, ...] = ()
    platforms: Tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkRef:
    title: str
    kind: WorkKind


@dataclass(frozen=True)
class UserWorkSpec:
    ref: WorkRef
    status: str
    rating: int | None
    progress: Decimal
    times_completed: int
    added_days_ago: int


@dataclass(frozen=True)
class CollectionSpec:
    name: str
    items: Tuple[WorkRef, ...] = ()
    children: Tuple["CollectionSpec", ...] = ()


@dataclass(frozen=True)
class RelationSpec:
    source: WorkRef
    target: WorkRef
    relation_type: str
