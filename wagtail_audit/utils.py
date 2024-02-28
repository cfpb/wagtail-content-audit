from wagtail.models import get_page_models


dotted_name = lambda cls: ".".join((cls.__module__, cls.__qualname__))


def get_page_models_and_fields(pagetypes=None):
    page_models = get_page_models()

    for page_model in page_models:
        for field in page_model._meta.concrete_fields:
            pagetype_str = (
                f"{page_model._meta.app_label}."
                f"{page_model._meta.object_name}."
                f"{field.name}"
            )
            if pagetypes is None or pagetype_str in pagetypes:
                yield page_model, field.name
