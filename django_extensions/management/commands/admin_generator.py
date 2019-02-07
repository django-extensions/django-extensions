# -*- coding: utf-8 -*-
"""
The Django Admin Generator is a project which can automatically generate
(scaffold) a Django Admin for you. By doing this it will introspect your
models and automatically generate an Admin with properties like:

 - `list_display` for all local fields
 - `list_filter` for foreign keys with few items
 - `raw_id_fields` for foreign keys with a lot of items
 - `search_fields` for name and `slug` fields
 - `prepopulated_fields` for `slug` fields
 - `date_hierarchy` for `created_at`, `updated_at` or `joined_at` fields

The original source and latest version can be found here:
https://github.com/WoLpH/django-admin-generator/
"""

import re
import sys

import six
from django.apps import apps
from django.conf import settings
from django.core.management.base import LabelCommand, CommandError
from django.db import models

from django_extensions.management.color import color_style
from django_extensions.management.utils import signalcommand

# Configurable constants
MAX_LINE_WIDTH = getattr(settings, 'MAX_LINE_WIDTH', 78)
INDENT_WIDTH = getattr(settings, 'INDENT_WIDTH', 4)
LIST_FILTER_THRESHOLD = getattr(settings, 'LIST_FILTER_THRESHOLD', 25)
RAW_ID_THRESHOLD = getattr(settings, 'RAW_ID_THRESHOLD', 100)

LIST_FILTER = getattr(settings, 'LIST_FILTER', (
    models.DateField,
    models.DateTimeField,
    models.ForeignKey,
    models.BooleanField,
))

SEARCH_FIELD_NAMES = getattr(settings, 'SEARCH_FIELD_NAMES', (
    'name',
    'slug',
))

DATE_HIERARCHY_NAMES = getattr(settings, 'DATE_HIERARCHY_NAMES', (
    'joined_at',
    'updated_at',
    'created_at',
))

PREPOPULATED_FIELD_NAMES = getattr(settings, 'PREPOPULATED_FIELD_NAMES', (
    'slug=name',
))

PRINT_IMPORTS = getattr(settings, 'PRINT_IMPORTS', '''# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import %(models)s
''')

PRINT_ADMIN_CLASS = getattr(settings, 'PRINT_ADMIN_CLASS', '''

@admin.register(%(name)s)
class %(name)sAdmin(admin.ModelAdmin):%(class_)s
''')

PRINT_ADMIN_PROPERTY = getattr(settings, 'PRINT_ADMIN_PROPERTY', '''
    %(key)s = %(value)s''')


class UnicodeMixin(object):
    """Mixin class to handle defining the proper __str__/__unicode__
    methods in Python 2 or 3."""

    if six.PY3:  # Python 3
        def __str__(self):
            return self.__unicode__()
    else:  # Python 2
        def __str__(self):
            return self.__unicode__().encode('utf8')


class AdminApp(UnicodeMixin):
    def __init__(self, app_config, model_res, **options):
        self.app_config = app_config
        self.model_res = model_res
        self.options = options

    def __iter__(self):
        for model in self.app_config.get_models():
            admin_model = AdminModel(model, **self.options)

            for model_re in self.model_res:
                if model_re.search(admin_model.name):
                    break
            else:
                if self.model_res:
                    continue

            yield admin_model

    def __unicode__(self):
        return ''.join(self._unicode_generator())

    def _unicode_generator(self):
        models_list = [admin_model.name for admin_model in self]
        yield PRINT_IMPORTS % dict(models=', '.join(models_list))

        admin_model_names = []
        for admin_model in self:
            yield PRINT_ADMIN_CLASS % dict(
                name=admin_model.name,
                class_=admin_model,
            )
            admin_model_names.append(admin_model.name)

    def __repr__(self):
        return '<%s[%s]>' % (
            self.__class__.__name__,
            self.app.name,
        )


class AdminModel(UnicodeMixin):
    PRINTABLE_PROPERTIES = (
        'list_display',
        'list_filter',
        'raw_id_fields',
        'search_fields',
        'prepopulated_fields',
        'date_hierarchy',
    )

    def __init__(self, model, raw_id_threshold=RAW_ID_THRESHOLD,
                 list_filter_threshold=LIST_FILTER_THRESHOLD,
                 search_field_names=SEARCH_FIELD_NAMES,
                 date_hierarchy_names=DATE_HIERARCHY_NAMES,
                 prepopulated_field_names=PREPOPULATED_FIELD_NAMES, **options):
        self.model = model
        self.list_display = []
        self.list_filter = []
        self.raw_id_fields = []
        self.search_fields = []
        self.prepopulated_fields = {}
        self.date_hierarchy = None
        self.search_field_names = search_field_names
        self.raw_id_threshold = raw_id_threshold
        self.list_filter_threshold = list_filter_threshold
        self.date_hierarchy_names = date_hierarchy_names
        self.prepopulated_field_names = prepopulated_field_names

    def __repr__(self):
        return '<%s[%s]>' % (
            self.__class__.__name__,
            self.name,
        )

    @property
    def name(self):
        return self.model.__name__

    def _process_many_to_many(self, meta):
        raw_id_threshold = self.raw_id_threshold
        for field in meta.local_many_to_many:
            if hasattr(field, 'remote_field'):
                related_model = getattr(field.remote_field, 'related_model', field.remote_field.model)
            else:
                raise CommandError("Unable to process ManyToMany relation")
            related_objects = related_model.objects.all()
            if related_objects[:raw_id_threshold].count() < raw_id_threshold:
                yield field.name

    def _process_fields(self, meta):
        parent_fields = meta.parents.values()
        for field in meta.fields:
            name = self._process_field(field, parent_fields)
            if name:
                yield name

    def _process_foreign_key(self, field):
        raw_id_threshold = self.raw_id_threshold
        list_filter_threshold = self.list_filter_threshold
        max_count = max(list_filter_threshold, raw_id_threshold)
        if hasattr(field, 'remote_field'):
            related_model = getattr(field.remote_field, 'related_model', field.remote_field.model)
        else:
            raise CommandError("Unable to process ForeignKey relation")
        related_count = related_model.objects.all()
        related_count = related_count[:max_count].count()

        if related_count >= raw_id_threshold:
            self.raw_id_fields.append(field.name)

        elif related_count < list_filter_threshold:
            self.list_filter.append(field.name)

        else:  # pragma: no cover
            pass  # Do nothing :)

    def _process_field(self, field, parent_fields):
        if field in parent_fields:
            return

        field_name = six.text_type(field.name)
        self.list_display.append(field_name)
        if isinstance(field, LIST_FILTER):
            if isinstance(field, models.ForeignKey):
                self._process_foreign_key(field)
            else:
                self.list_filter.append(field_name)

        if field.name in self.search_field_names:
            self.search_fields.append(field_name)

        return field_name

    def __unicode__(self):
        return ''.join(self._unicode_generator())

    def _yield_value(self, key, value):
        if isinstance(value, (list, set, tuple)):
            return self._yield_tuple(key, tuple(value))
        elif isinstance(value, dict):
            return self._yield_dict(key, value)
        elif isinstance(value, str):
            return self._yield_string(key, value)
        else:  # pragma: no cover
            raise TypeError('%s is not supported in %r' % (type(value), value))

    def _yield_string(self, key, value, converter=repr):
        return PRINT_ADMIN_PROPERTY % dict(
            key=key,
            value=converter(value),
        )

    def _yield_dict(self, key, value):
        row_parts = []
        row = self._yield_string(key, value)
        if len(row) > MAX_LINE_WIDTH:
            row_parts.append(self._yield_string(key, '{', str))
            for k, v in value.items():
                row_parts.append('%s%r: %r' % (2 * INDENT_WIDTH * ' ', k, v))

            row_parts.append(INDENT_WIDTH * ' ' + '}')
            row = '\n'.join(row_parts)

        return row

    def _yield_tuple(self, key, value):
        row_parts = []
        row = self._yield_string(key, value)
        if len(row) > MAX_LINE_WIDTH:
            row_parts.append(self._yield_string(key, '(', str))
            for v in value:
                row_parts.append(2 * INDENT_WIDTH * ' ' + repr(v) + ',')

            row_parts.append(INDENT_WIDTH * ' ' + ')')
            row = '\n'.join(row_parts)

        return row

    def _unicode_generator(self):
        self._process()
        for key in self.PRINTABLE_PROPERTIES:
            value = getattr(self, key)
            if value:
                yield self._yield_value(key, value)

    def _process(self):
        meta = self.model._meta

        self.raw_id_fields += list(self._process_many_to_many(meta))
        field_names = list(self._process_fields(meta))

        for field_name in self.date_hierarchy_names[::-1]:
            if field_name in field_names and not self.date_hierarchy:
                self.date_hierarchy = field_name
                break

        for k in sorted(self.prepopulated_field_names):
            k, vs = k.split('=', 1)
            vs = vs.split(',')
            if k in field_names:
                incomplete = False
                for v in vs:
                    if v not in field_names:
                        incomplete = True
                        break

                if not incomplete:
                    self.prepopulated_fields[k] = vs

        self.processed = True


class Command(LabelCommand):
    help = '''Generate a `admin.py` file for the given app (models)'''
    # args = "[app_name]"
    can_import_settings = True

    def add_arguments(self, parser):
        parser.add_argument('app_name')
        parser.add_argument('model_name', nargs='*')
        parser.add_argument(
            '-s', '--search-field', action='append',
            default=SEARCH_FIELD_NAMES,
            help='Fields named like this will be added to `search_fields`'
            ' [default: %(default)s]')
        parser.add_argument(
            '-d', '--date-hierarchy', action='append',
            default=DATE_HIERARCHY_NAMES,
            help='A field named like this will be set as `date_hierarchy`'
            ' [default: %(default)s]')
        parser.add_argument(
            '-p', '--prepopulated-fields', action='append',
            default=PREPOPULATED_FIELD_NAMES,
            help='These fields will be prepopulated by the other field.'
            'The field names can be specified like `spam=eggA,eggB,eggC`'
            ' [default: %(default)s]')
        parser.add_argument(
            '-l', '--list-filter-threshold', type=int,
            default=LIST_FILTER_THRESHOLD, metavar='LIST_FILTER_THRESHOLD',
            help='If a foreign key has less than LIST_FILTER_THRESHOLD items '
            'it will be added to `list_filter` [default: %(default)s]')
        parser.add_argument(
            '-r', '--raw-id-threshold', type=int,
            default=RAW_ID_THRESHOLD, metavar='RAW_ID_THRESHOLD',
            help='If a foreign key has more than RAW_ID_THRESHOLD items '
            'it will be added to `list_filter` [default: %(default)s]')

    @signalcommand
    def handle(self, *args, **options):
        self.style = color_style()

        app_name = options['app_name']
        try:
            app = apps.get_app_config(app_name)
        except LookupError:
            print(self.style.WARN('This command requires an existing app name as argument'))
            print(self.style.WARN('Available apps:'))
            app_labels = [app.label for app in apps.get_app_configs()]
            for label in sorted(app_labels):
                print(self.style.WARN('    %s' % label))
            sys.exit(1)

        model_res = []
        for arg in options['model_name']:
            model_res.append(re.compile(arg, re.IGNORECASE))

        self.stdout.write(AdminApp(app, model_res, **options).__str__())
