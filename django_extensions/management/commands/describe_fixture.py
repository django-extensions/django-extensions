import logging

from django.core.management.base import AppCommand
from django.core import serializers
import django.db.models as django_models
from django.db.models import get_models
from django import db
# from django.core.management.command import dumpdata

logger = logging.getLogger(__name__)

class Command(AppCommand):
    help = "Generates a testing fixture for the given app that you should put in APP/fixture.py."
    args = "[appname]"
    label = "application name"

    def handle_app(self, app, **options):
        return describe_fixture(app)


def describe_fixture(app, **options):
    # TODO: try to use the dumpdata command from Django.core
    # to get the serialized data instead of re-inventing the wheel
    # UPDATE: can't use django.core dumpdata because it would
    # require refactoring of that command
    models_module = app
    samples = []
    for model in get_models(models_module):
        # get n of them
        try:
            samples.extend(list(model.objects.order_by('pk')[:5]))
        except Exception as e:
            logger.error(e)
    # serialized those n
    output = serializers.serialize('json', samples, indent=4)
    # output them
    return output


def yield_field_names(model):
    for field in model._meta.fields:
        if not isinstance(field, db.models.fields.related.RelatedField):
            yield field.name

