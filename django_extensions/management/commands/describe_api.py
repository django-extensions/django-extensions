from django.core.management.base import AppCommand
import django.db.models as django_models
from django.db.models import get_models


class Command(AppCommand):
    help = "Generates tastypie resources for the given app that you should put in APP/api.py."
    args = "[appname]"
    label = "application name"

    def handle_app(self, app, **options):
        return describe_api(app)


FIELD_TEMPLATE = "{attribute_name} = fields.ForeignKey('{app_name}.api.{foreign_model}', '{attribute_name}'{options_str})"
RESOURCE_POSTFIX = 'Resource'


def describe_api(app, **options):
    """
    Returns a string representing a barebone but functional api module for the given app.
    The tastypie Resources described in this string have ForeignKey fields with resonable defaults and
    some options taken directly from the models' fields.

    Currently the returned resources only have the forward part of a ToOne relationship. It does not handle ToMany relationships
    and the backward part of a relationship.
    """
    models_module = app
    all_models = []
    all_resources = []
    all_resources_names = []

    for model in get_models(models_module):
        fields_str = '\n'.join(yield_field_strings(model))
        filtering_fields = ('\n'+' '*20).join(yield_filtering_fields(model))
        filtering_str = META_FILTERING_TEMPLATE.format(filtering_fields=filtering_fields)
        resource_str = build_resource_str(model, fields=fields_str, filtering=filtering_str)

        model_name = model._meta.object_name
        all_models.append(model_name)
        all_resources.append(resource_str)
        all_resources_names.append(model_name+RESOURCE_POSTFIX)

    return API_MODULE.format(all_models=', '.join(all_models), all_resources='\n'.join(all_resources), all_resources_names=', '.join(all_resources_names))


def yield_field_strings(model):
    options = model._meta
    app_name = options.app_label
    for field in options.fields:
        if isinstance(field, django_models.ForeignKey):
            attribute_name = field.name
            # no support for m2m yet
            foreign_model = field.get_path_info()[0].to_opts.object_name
            options_str = ', ' + ', '.join(yield_field_options(field))
            if not options_str.strip(', '):
                options_str = ''
            yield FIELD_TEMPLATE.format(attribute_name=attribute_name, app_name=app_name,
                foreign_model=foreign_model+RESOURCE_POSTFIX, options_str=options_str)


def yield_field_options(field):
    options = {'null': field.null,
            'blank': field.blank,
            'related_name': field.related_query_name().join("''"),
            'help_text': bool(field.help_text) and repr(field.help_text) or '',
            }
    for key, val in options.items():
        if val:
            yield '='.join([key, str(val)])


META_FILTERING_TEMPLATE = "filtering = {{{filtering_fields}}}\n"
FIELD_FILTERING_TEMPLATE = "'{field}': {mode},"


def yield_filtering_fields(model):
    options = model._meta
    for field in options.fields:
        attribute_name = field.name
        if isinstance(field, django_models.ForeignKey):
            yield FIELD_FILTERING_TEMPLATE.format(field=attribute_name, mode='resources.ALL_WITH_RELATIONS')
        else:
            yield FIELD_FILTERING_TEMPLATE.format(field=attribute_name, mode='resources.ALL')


IMPORTS_TEMPLATE = """# This is an auto-generated Django-tastypie api module.
# You'll have to do the following manually to clean this up:
#   * Manually add ToMany relationships fields between Resources (optional)
#   * Manually add the back references of the current forward references (optional)
#        (see http://django-tastypie.readthedocs.org/en/latest/fields.html#tastypie.fields.RelatedField.related_name)
#
# Feel free to rename the resources, but if you do so, chage it everywhere
# (don't forget to change it inside the ALL_RESOURCES list at the end of the module)
#
# also add the following to your <project>/<url.py>
#
# from tastypie.api import Api
#
# from <app_name> import api
#
# # api hookup
# v1_api = Api(api_name='v1')
# for resource in api.ALL_RESOURCES:
#   v1_api.register(resource())
#
# # add the api urls to the url patterns
# urlpatterns = patterns('',
#   ...
#     url(r'^api/', include(v1_api.urls)),
#     ...
#     )


from tastypie import resources, fields

from .models import {all_models}


"""

RESOURCE_TEMPLATE = "class {model_name}"+RESOURCE_POSTFIX+"""(resources.ModelResource):
    {fields}

    class Meta:
        queryset = {model_name}.objects.all()
        {filtering}

"""
FOOTER_TEMPLATE = 'ALL_RESOURCES = [{all_resources_names}]'
API_MODULE = IMPORTS_TEMPLATE + '{all_resources}\n' + FOOTER_TEMPLATE


def build_resource_str(model, fields='{fields}', filtering=''):
    model_name = model._meta.object_name
    fields = fields.replace('\n', '\n'+' '*4)
    return RESOURCE_TEMPLATE.format(model_name=model_name, fields=fields, filtering=filtering).replace('\n    \n\n', '\n'*1)
