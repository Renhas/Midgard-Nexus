from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.contenttypes.models import ContentType

from ..constants import RELATION_SCOPES, RelationScope, WorkRelationTypeChoices


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
        raise ValidationError(f"Объект с типом {ct} и ID {obj_id} не существует.")


def validate_relation_type(
    source_ct: ContentType,
    target_ct: ContentType,
    relation_type: WorkRelationTypeChoices | str,
) -> None:
    """
    Проверяет, допустима ли связь между типами произведений по RELATION_SCOPES.
    """
    scope = RELATION_SCOPES.get(
        WorkRelationTypeChoices(relation_type), RelationScope.SAME
    )
    if scope == RelationScope.ANY:
        return
    same_type = source_ct == target_ct
    if scope == RelationScope.DIFFERENT and same_type:
        raise ValidationError(
            f"Связь '{relation_type}' допустима только между произведениями разных типов."
        )
    if scope == RelationScope.SAME and not same_type:
        raise ValidationError(
            f"Связь '{relation_type}' допустима только между произведениями одного типа."
        )
