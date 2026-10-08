from django.db import migrations


def backfill_order_position(apps, schema_editor):
    UserWork = apps.get_model("vor_archives", "UserWork")
    user_ids = UserWork.objects.values_list("user_id", flat=True).distinct()
    for user_id in user_ids:
        works = list(
            UserWork.objects.filter(user_id=user_id).order_by("date_added", "pk")
        )
        changed = []
        for index, user_work in enumerate(works):
            if user_work.order_position != index:
                user_work.order_position = index
                changed.append(user_work)
        if changed:
            UserWork.objects.bulk_update(changed, ["order_position"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("vor_archives", "0006_userwork_unique_user_work"),
    ]

    operations = [
        migrations.RunPython(backfill_order_position, noop),
    ]
