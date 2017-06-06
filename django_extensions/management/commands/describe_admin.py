from django.core.management.base import AppCommand
import django.db.models as django_models
from django.db.models import get_models

LIST_PER_PAGE_DEFAULT = 30


class Command(AppCommand):
    help = "Generates ModelAdmin for the given app that you should put in <APP>/admin.py."
    args = "[appname]"
    label = "application name"

    def handle_app(self, app, **options):
        return describe_admin(app)


IMPORTS_TEMPLATE = """# disclaimers and instructions
from django.contrib import admin

from .models import {all_models}


{all_admins}
"""

ADMIN_POSTFIX = "Admin"
# for django 1.7 we might need to add `@admin.register({model_name})` here
# see: https://docs.djangoproject.com/en/dev/ref/contrib/admin/#django.contrib.admin.register
ADMIN_TEMPLATE = "class {model_name}" + ADMIN_POSTFIX + """(admin.ModelAdmin):
    list_per_page = {page_size}
    {options}

admin.site.register({model_name}, {model_name}""" + ADMIN_POSTFIX + """)


"""
RAW_ID_FIELDS_TEMPLATE = "raw_id_fields = {fields_list}"
SEARCH_FIELDS_TEMPLATE = "search_fields = {fields_list}"
LIST_DISPLAY_TEMPLATE = "list_display = {fields_list}"
LIST_FILTER_TEMPLATE = "list_filter = {fields_list}"

ADMIN_MODULE_TEMPLATE = IMPORTS_TEMPLATE


def describe_admin(models_module, page_size=LIST_PER_PAGE_DEFAULT):
    all_model_names = ', '.join([model._meta.object_name for model in get_models(models_module)])
    all_admins = ''.join([describe_admin_model(model) for model in get_models(models_module)])
    return ADMIN_MODULE_TEMPLATE.format(all_models=all_model_names,
                                        all_admins=all_admins
                                        ).format(page_size=page_size)


def describe_admin_model(model):
    model_name = model._meta.object_name
    # admin_name =
    # all_model_names
    raw_id_fields_str = repr(tuple(yield_raw_id_fields(model)))
    search_fields_str = repr(tuple(yield_search_fields(model)))
    list_display_str = repr(tuple(yield_list_display(model)))
    list_filter_str = repr(tuple(yield_list_filter(model)))

    options = []
    if raw_id_fields_str:
        options.append(RAW_ID_FIELDS_TEMPLATE.format(fields_list=raw_id_fields_str))
    if search_fields_str:
        options.append(SEARCH_FIELDS_TEMPLATE.format(fields_list=search_fields_str))
    if list_display_str:
        options.append(LIST_DISPLAY_TEMPLATE.format(fields_list=list_display_str))
    if list_filter_str:
        options.append(LIST_FILTER_TEMPLATE.format(fields_list=list_filter_str))

    model_str = ADMIN_TEMPLATE.format(model_name=model_name,
                                      page_size='{page_size}',
                                      options='\n    '.join(options))
    return model_str


def yield_raw_id_fields(model):
    # raw_id_fields are all relationship fields
    # the raw_id_fields help avoiding extra queries on the DB.
    candidate_fields = [field for field in model._meta.fields if isinstance(field, django_models.ForeignKey)]
    for field in candidate_fields:
        yield field.name


def yield_search_fields(model):
    # a good search fields could be:
    # IntegerField, CharField,
    candidate_fields = [field for field in model._meta.fields if
                        isinstance(field, (django_models.IntegerField,
                                           django_models.CharField,
                                           django_models.TextField,
                                           ))]
    for field in candidate_fields:
            yield field.name


def yield_list_display(model):
    # good list_display fields are:
    # BooleanField, CharField, IntegerField, DecimalField, etc
    # in fact all fields would be good fields, with the possible
    # exception of relationships fields
    candidate_fields = [field for field in model._meta.fields]
    for field in candidate_fields:
            yield field.name


def yield_list_filter(model):
    # good list_filter fields are:
    # BooleanField, DateField, ChoiceField,
    # and relationships fields that have a limited number of options
    candidate_fields = set(field for field in model._meta.fields if
                           isinstance(field, (django_models.BooleanField,
                                              django_models.DateField,
                                              )))
    choice_fields = set(yield_choice_fields(model))
    for field in sorted(candidate_fields.union(choice_fields)):
            yield field.name


def yield_choice_fields(model, choice_max_size=25):
    for field in model._meta.fields:
        # if isinstance(field, django_models.ForeignKey):
        #     if field.model.objects.count() < choice_max_size:
        #         yield field
        # elif field.choices:
        if field.choices:
            yield field
