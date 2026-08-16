from django.db import migrations, models
from django.db.models import Count, Min


def dedupe_user_works(apps, schema_editor):
    UserWork = apps.get_model("vor_archives", "UserWork")
    dupes = (
        UserWork.objects.values("user", "work_content_type", "work_object_id")
        .annotate(n=Count("id"), keep=Min("id"))
        .filter(n__gt=1)
    )
    for row in dupes:
        UserWork.objects.filter(
            user_id=row["user"],
            work_content_type_id=row["work_content_type"],
            work_object_id=row["work_object_id"],
        ).exclude(pk=row["keep"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("vor_archives", "0005_film_check_episode_count_by_type"),
    ]

    operations = [
        migrations.RunPython(dedupe_user_works, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="userwork",
            constraint=models.UniqueConstraint(
                fields=("user", "work_content_type", "work_object_id"),
                name="unique_user_work",
            ),
        ),
    ]
