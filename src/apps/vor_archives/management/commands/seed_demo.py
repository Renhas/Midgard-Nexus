"""Seed ``vor_archives`` with demo data.

Idempotent: re-runs do not duplicate rows or overwrite covers.
Use ``--clear`` to wipe everything the seeder (and any manual tests) created,
except the users themselves.
"""

from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile, File
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.vor_archives.constants import (
    FeedItemActionTypeChoices,
    UserWorkStatusChoices,
)
from apps.vor_archives.models import (
    Book,
    BookGenre,
    Collection,
    CollectionItem,
    CompletionRecord,
    FeedItem,
    Film,
    FilmGenre,
    Game,
    GameGenre,
    Person,
    Platform,
    Tag,
    UserWork,
    WorkRelation,
)

from .seed_data import attributes as attr_meta
from .seed_data import collections as collections_data
from .seed_data import user_data
from .seed_data import works as works_data
from .seed_data.placeholders import render_placeholder, slugify_title
from .seed_data.types import BookSpec, FilmSpec, GameSpec

# extensions checked in order
_EXT_ORDER = (".png", ".jpg", ".jpeg", ".webp")
COVERS_DIR = Path(__file__).resolve().parent / "seed_data" / "covers"


class Command(BaseCommand):
    help = "Seed vor_archives with demo data (idempotent). Use --clear to wipe first."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete seeder-owned data before seeding.",
        )

    # ── entrypoint ──────────────────────────────────────────────────────────

    def handle(self, *args, **options) -> None:
        if options["clear"]:
            self.stdout.write("🧹 Clearing existing demo data…")
            self._clear()

        admin = self._get_admin()

        with transaction.atomic():
            self.stdout.write("🎬 Seeding works…")
            works = self._seed_works()

            self.stdout.write("🔗 Seeding relations…")
            self._seed_relations(works)

            self.stdout.write("👤 Seeding user activity…")
            self._seed_user_works(admin, works)

            self.stdout.write("🗂  Seeding collections…")
            self._seed_collections(admin, works)

        self.stdout.write(self.style.SUCCESS("✅ seed_demo finished."))

    # ── admin ───────────────────────────────────────────────────────────────

    def _get_admin(self):
        User = get_user_model()
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME") or "admin"
        admin = User.objects.filter(username=username).first()
        if admin is None:
            raise CommandError(
                f"Superuser '{username}' not found. The seed command attaches demo "
                "activity to an existing user. Start the project via docker-compose "
                "(entrypoint creates the superuser) or create it manually."
            )
        return admin

    # ── clear ───────────────────────────────────────────────────────────────

    def _clear(self) -> None:
        with transaction.atomic():
            for model in (
                FeedItem,
                CompletionRecord,
                UserWork,
                CollectionItem,
                Collection,
                WorkRelation,
                Book,
                Film,
                Game,
                Person,
                Platform,
                BookGenre,
                FilmGenre,
                GameGenre,
                Tag,
            ):
                model.objects.all().delete()

    # ── attributes ──────────────────────────────────────────────────────────

    def _resolve(self, model, names, description_map=None):
        """get_or_create for attribute models. Descriptions applied on first create only."""
        description_map = description_map or {}
        fields = {f.name for f in model._meta.fields}
        has_description = "description" in fields
        result = []
        for name in names:
            defaults = {}
            if has_description and name in description_map:
                defaults["description"] = description_map[name]
            obj, _ = model.objects.get_or_create(name=name, defaults=defaults)
            result.append(obj)
        return result

    # ── works ───────────────────────────────────────────────────────────────

    def _seed_works(self) -> dict[tuple[str, str], object]:
        works: dict[tuple[str, str], object] = {}
        for spec in works_data.BOOKS:
            works[(spec.title, "book")] = self._upsert_book(spec)
        for spec in works_data.FILMS:
            works[(spec.title, "film")] = self._upsert_film(spec)
        for spec in works_data.GAMES:
            works[(spec.title, "game")] = self._upsert_game(spec)
        return works

    def _upsert_book(self, spec: BookSpec) -> Book:
        work, created = Book.objects.get_or_create(
            title=spec.title,
            defaults={
                "release_date": spec.release_date,
                "description": spec.description,
                "age_rating": spec.age_rating,
                "external_link": spec.external_link,
                "pages": spec.pages,
            },
        )
        if created:
            work.authors.set(self._resolve(Person, spec.authors, attr_meta.PERSON_BIOS))
            work.tags.set(self._resolve(Tag, spec.tags, attr_meta.TAG_DESCRIPTIONS))
            work.genres.set(
                self._resolve(BookGenre, spec.genres, attr_meta.GENRE_DESCRIPTIONS)
            )
            self._attach_cover(work, kind="book", spec=spec)
        return work

    def _upsert_film(self, spec: FilmSpec) -> Film:
        work, created = Film.objects.get_or_create(
            title=spec.title,
            defaults={
                "release_date": spec.release_date,
                "description": spec.description,
                "age_rating": spec.age_rating,
                "external_link": spec.external_link,
                "duration_minutes": spec.duration_minutes,
                "film_type": spec.film_type,
                "episode_count": spec.episode_count,
            },
        )
        if created:
            work.authors.set(self._resolve(Person, spec.authors, attr_meta.PERSON_BIOS))
            work.tags.set(self._resolve(Tag, spec.tags, attr_meta.TAG_DESCRIPTIONS))
            work.genres.set(
                self._resolve(FilmGenre, spec.genres, attr_meta.GENRE_DESCRIPTIONS)
            )
            self._attach_cover(work, kind="film", spec=spec)
        return work

    def _upsert_game(self, spec: GameSpec) -> Game:
        work, created = Game.objects.get_or_create(
            title=spec.title,
            defaults={
                "release_date": spec.release_date,
                "description": spec.description,
                "age_rating": spec.age_rating,
                "external_link": spec.external_link,
            },
        )
        if created:
            work.authors.set(self._resolve(Person, spec.authors, attr_meta.PERSON_BIOS))
            work.tags.set(self._resolve(Tag, spec.tags, attr_meta.TAG_DESCRIPTIONS))
            work.genres.set(
                self._resolve(GameGenre, spec.genres, attr_meta.GENRE_DESCRIPTIONS)
            )
            work.platforms.set(self._resolve(Platform, spec.platforms))
            self._attach_cover(work, kind="game", spec=spec)
        return work

    # ── covers ──────────────────────────────────────────────────────────────

    def _attach_cover(self, work, *, kind, spec):
        """Idempotent: only acts if work has no cover, or if current cover is a
        generated placeholder and a real file has appeared in covers/ since last run."""
        slug = slugify_title(spec.title)

        real_path = next(
            (
                COVERS_DIR / f"{kind}_{slug}{ext}"
                for ext in _EXT_ORDER
                if (COVERS_DIR / f"{kind}_{slug}{ext}").exists()
            ),
            None,
        )

        current = work.cover.name if work.cover else ""
        is_generated = current.rsplit("/", 1)[-1].startswith("_gen_")

        if current and not is_generated:
            return  # real cover already attached → leave it

        if real_path is not None and (not current or is_generated):
            with real_path.open("rb") as fh:
                work.cover.save(real_path.name, File(fh), save=True)
            return

        if current:  # placeholder already in place → leave it
            return

        png = render_placeholder(kind=kind, title=spec.title, authors=spec.authors)
        work.cover.save(f"_gen_{kind}_{slug}.png", ContentFile(png), save=True)

    # ── relations ───────────────────────────────────────────────────────────

    def _seed_relations(self, works: dict) -> None:
        for rel in works_data.RELATIONS:
            src = works.get((rel.source.title, rel.source.kind))
            dst = works.get((rel.target.title, rel.target.kind))
            if src is None or dst is None:
                continue
            if WorkRelation.objects.filter(source=src, target=dst).exists():
                continue
            WorkRelation.objects.create(
                source=src, target=dst, relation_type=rel.relation_type
            )

    # ── user activity (UserWork + FeedItem + CompletionRecord) ──────────────

    def _seed_user_works(self, admin, works: dict) -> None:
        now = timezone.now()
        for spec in user_data.USER_WORKS:
            work = works.get((spec.ref.title, spec.ref.kind))
            if work is None:
                self.stderr.write(f"⚠️  Work not found: {spec.ref}")
                continue

            content_type = ContentType.objects.get_for_model(work)

            # Idempotency: skip anything already attached to this user.
            if UserWork.objects.filter(
                user=admin,
                work_content_type=content_type,
                work_object_id=work.pk,
            ).exists():
                continue

            # Two-step create, same workaround as the test suite.
            # `userwork_pre_save` (signals.py) fires from pre_save and tries
            # to create CompletionRecord(user_work=instance); at that point
            # the instance has no pk yet → ValueError. So we create with the
            # default status and patch the real fields through queryset.update(),
            # which bypasses signals and auto_now_add entirely.
            # TODO: collapse into a single create once the signal is fixed.
            uw = UserWork.objects.create(
                user=admin,
                work_content_type=content_type,
                work_object_id=work.pk,
                status=UserWorkStatusChoices.PLANNING,
            )

            added_at = now - timedelta(days=spec.added_days_ago)
            UserWork.objects.filter(pk=uw.pk).update(
                status=spec.status,
                rating=spec.rating,
                progress=spec.progress,
                times_completed=spec.times_completed,
                date_added=added_at,  # auto_now_add is bypassed by .update()
            )
            uw.refresh_from_db()

            self._emit_feed_items(uw, added_at)
            if uw.status == UserWorkStatusChoices.COMPLETED:
                self._emit_completion(uw, added_at)

    def _emit_feed_items(self, uw: UserWork, added_at) -> None:
        A = FeedItemActionTypeChoices
        status = uw.status

        actions = [A.ADDED]
        if status in (
            UserWorkStatusChoices.IN_PROGRESS,
            UserWorkStatusChoices.COMPLETED,
            UserWorkStatusChoices.DROPPED,
        ):
            actions.append(A.IN_PROGRESS)
        if status == UserWorkStatusChoices.COMPLETED:
            actions.append(A.COMPLETED)
        if status == UserWorkStatusChoices.DROPPED:
            actions.append(A.DROPPED)
        if uw.rating:
            actions.append(A.RATED)

        step_days = 3 if status == UserWorkStatusChoices.COMPLETED else 7
        now = timezone.now()
        for idx, action in enumerate(actions):
            ts = added_at + timedelta(days=idx * step_days)
            if ts > now:
                ts = now
            item = FeedItem.objects.create(
                user=uw.user, user_work=uw, action_type=action
            )
            # `timestamp` is auto_now_add -> bypass via queryset .update().
            FeedItem.objects.filter(pk=item.pk).update(timestamp=ts)

    def _emit_completion(self, uw: UserWork, added_at) -> None:
        now = timezone.now()
        when = added_at + timedelta(days=14)
        if when > now:
            when = now
        record = CompletionRecord.objects.create(user_work=uw)
        CompletionRecord.objects.filter(pk=record.pk).update(date=when)
        UserWork.objects.filter(pk=uw.pk).update(last_completed_date=when.date())

    # ── collections ─────────────────────────────────────────────────────────

    def _seed_collections(self, admin, works: dict) -> None:
        for spec in collections_data.COLLECTIONS:
            self._create_collection(admin, spec, parent=None, works=works)

    def _create_collection(self, admin, spec, *, parent, works: dict) -> Collection:
        coll, _ = Collection.objects.get_or_create(
            user=admin, name=spec.name, parent=parent
        )
        for idx, ref in enumerate(spec.items):
            work = works.get((ref.title, ref.kind))
            if work is None:
                continue
            CollectionItem.objects.get_or_create(
                collection=coll,
                work_content_type=ContentType.objects.get_for_model(work),
                work_object_id=work.pk,
                defaults={"order": idx},
            )
        for child in spec.children:
            self._create_collection(admin, child, parent=coll, works=works)
        return coll
