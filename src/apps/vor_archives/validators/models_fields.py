from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.contenttypes.models import ContentType

from ..constants import WorkRelationTypeChoices


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


def validate_relation_type(source_ct: ContentType, target_ct: ContentType, relation_type: WorkRelationTypeChoices | str) -> None:
    """
    Проверяет, допустима ли связь между типами произведений для данного relation_type.
    
    - 'other' — допустима для любых типов
    - 'adaptation' — только между разными типами
    - остальное — только между одинаковыми типами
    """
    if relation_type == WorkRelationTypeChoices.OTHER:
        return
    same_type = (source_ct == target_ct)
    if relation_type == WorkRelationTypeChoices.ADAPTATION and same_type:
        raise ValidationError(
            f"Связь '{relation_type}' допустима только между произведениями разных типов."
        )
    if relation_type != WorkRelationTypeChoices.ADAPTATION and not same_type:
        raise ValidationError(
            f"Связь '{relation_type}' допустима только между произведениями одного типа."
        )

