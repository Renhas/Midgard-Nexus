"""factory-boy factories for apps.vor_archives."""

import factory
from django.contrib.contenttypes.models import ContentType

from apps.users.tests.factories import UserFactory
from apps.vor_archives.constants import FilmTypeChoices, WorkRelationTypeChoices
from apps.vor_archives.models import (
    Book,
    BookGenre,
    Collection,
    CollectionItem,
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


class PersonFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Person
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Person {n}")


class PlatformFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Platform
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Platform {n}")


class BookGenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BookGenre
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Book genre {n}")


class FilmGenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FilmGenre
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Film genre {n}")


class GameGenreFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GameGenre
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Game genre {n}")


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag
        skip_postgeneration_save = True

    name = factory.Sequence(lambda n: f"Tag {n}")


class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book
        skip_postgeneration_save = True

    title = factory.Sequence(lambda n: f"Book {n}")
    pages = 300


class FilmFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Film
        skip_postgeneration_save = True

    title = factory.Sequence(lambda n: f"Film {n}")
    duration_minutes = 120
    film_type = FilmTypeChoices.MOVIE
    episode_count = None

    class Params:
        tv = factory.Trait(
            film_type=FilmTypeChoices.TV_SHOW,
            episode_count=10,
        )


class GameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Game
        skip_postgeneration_save = True

    title = factory.Sequence(lambda n: f"Game {n}")


class WorkRelationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WorkRelation
        exclude = ("source", "target")
        skip_postgeneration_save = True

    source = factory.SubFactory(BookFactory)
    target = factory.SubFactory(BookFactory)
    source_content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.source)
    )
    source_object_id = factory.LazyAttribute(lambda o: o.source.pk)
    target_content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.target)
    )
    target_object_id = factory.LazyAttribute(lambda o: o.target.pk)
    relation_type = WorkRelationTypeChoices.SEQUEL


class UserWorkFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserWork
        exclude = ("work",)
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    work = factory.SubFactory(BookFactory)
    work_content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.work)
    )
    work_object_id = factory.LazyAttribute(lambda o: o.work.pk)


class CollectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Collection
        skip_postgeneration_save = True

    user = factory.SubFactory(UserFactory)
    name = factory.Sequence(lambda n: f"Collection {n}")
    parent = None


class CollectionItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CollectionItem
        exclude = ("work",)
        skip_postgeneration_save = True

    collection = factory.SubFactory(CollectionFactory)
    work = factory.SubFactory(BookFactory)
    work_content_type = factory.LazyAttribute(
        lambda o: ContentType.objects.get_for_model(o.work)
    )
    work_object_id = factory.LazyAttribute(lambda o: o.work.pk)
