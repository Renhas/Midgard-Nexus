from django.db import migrations, models
from django.db.models import Count, Min


def backfill_collection_order(apps, schema_editor):
    Collection = apps.get_model("vor_archives", "Collection")
    groups = {}
    for collection in Collection.objects.all().order_by("name", "pk"):
        groups.setdefault((collection.user_id, collection.parent_id), []).append(collection)
    changed = []
    for siblings in groups.values():
        for index, collection in enumerate(siblings):
            if collection.order != index:
                collection.order = index
                changed.append(collection)
    if changed:
        Collection.objects.bulk_update(changed, ["order"])


def rebuild_collections(apps, schema_editor):
    from apps.vor_archives.models import Collection

    Collection.objects.rebuild()


def dedupe_collection_items(apps, schema_editor):
    CollectionItem = apps.get_model("vor_archives", "CollectionItem")
    dupes = (
        CollectionItem.objects.values("collection", "work_content_type", "work_object_id")
        .annotate(n=Count("id"), keep=Min("id"))
        .filter(n__gt=1)
    )
    for row in dupes:
        CollectionItem.objects.filter(
            collection_id=row["collection"],
            work_content_type_id=row["work_content_type"],
            work_object_id=row["work_object_id"],
        ).exclude(pk=row["keep"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("vor_archives", "0007_backfill_userwork_order_position"),
    ]

    operations = [
        migrations.AddField(
            model_name="collection",
            name="order",
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(backfill_collection_order, migrations.RunPython.noop),
        migrations.RunPython(rebuild_collections, migrations.RunPython.noop),
        migrations.RunPython(dedupe_collection_items, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="collectionitem",
            constraint=models.UniqueConstraint(
                fields=("collection", "work_content_type", "work_object_id"),
                name="vor_archives_collectionitem_unique_work",
            ),
        ),
    ]
