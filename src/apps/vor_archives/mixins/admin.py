from django.contrib.contenttypes.models import ContentType

ALLOWED_MODELS = ["book", "film", "series", "game"]
ALLOWED_CONTENTTYPES = ContentType.objects.filter(model__in=ALLOWED_MODELS, app_label='vor_archives')

class RestrictedContentTypeAdminMixin:
    restricted_ct_fields = []

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in self.restricted_ct_fields:
            kwargs["queryset"] = ALLOWED_CONTENTTYPES
        return super().formfield_for_foreignkey(db_field, request, **kwargs) # type: ignore
