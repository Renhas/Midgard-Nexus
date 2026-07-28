from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.contenttypes.models import ContentType


def validate_gfk(ct: ContentType | None, obj_id: int | None) -> None:
    """
    Проверяет, что объект с заданным content_type и object_id существует.
    Если ct или obj_id равны None, проверка пропускается.
    """
    if ct is None or obj_id is None:
        return
    try:
        ct.get_object_for_this_type(pk=obj_id)
    except ObjectDoesNotExist:
        raise ValidationError(
            f"Объект с типом {ct} и ID {obj_id} не существует."
        )
    