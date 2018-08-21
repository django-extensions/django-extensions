# -*- coding: utf-8 -*-
"""
sqldiff.py - Prints the (approximated) difference between models and database

TODO:
 - better support for relations
 - better support for constraints (mainly postgresql?)
 - support for table spaces with postgresql
 - when a table is not managed (meta.managed==False) then only do a one-way
   sqldiff ? show differences from db->table but not the other way around since
   it's not managed.

KNOWN ISSUES:
 - MySQL has by far the most problems with introspection. Please be
   carefull when using MySQL with sqldiff.
   - Booleans are reported back as Integers, so there's no way to know if
     there was a real change.
   - Varchar sizes are reported back without unicode support so their size
     may change in comparison to the real length of the varchar.
   - Some of the 'fixes' to counter these problems might create false
     positives or false negatives.
"""

import importlib
import sys
import six
import argparse
from typing import Dict, Union, Callable, Optional  # NOQA
from django.apps import apps
from django.core.management import BaseCommand, CommandError
from django.core.management.base import OutputWrapper
from django.core.management.color import no_style
from django.db import connection, transaction, models
from django.db.models.fields import AutoField, IntegerField

from django_extensions.management.utils import signalcommand

ORDERING_FIELD = IntegerField('_order', null=True)


def flatten(lst, ltypes=(list, tuple)):
    ltype = type(lst)
    lst = list(lst)
    i = 0
    while i < len(lst):
        while isinstance(lst[i], ltypes):
            if not lst[i]:
                lst.pop(i)
                i -= 1
                break
            else:
                lst[i:i + 1] = lst[i]
        i += 1
    return ltype(lst)


def all_local_fields(meta):
    all_fields = []
    if meta.proxy:
        for parent in meta.parents:
            all_fields.extend(all_local_fields(parent._meta))
    else:
        for f in meta.local_fields:
            col_type = f.db_type(connection=connection)
            if col_type is None:
                continue
            all_fields.append(f)
    return all_fields


class SQLDiff(object):
    DATA_TYPES_REVERSE_OVERRIDE = {}  # type: Dict[int, Union[str, Callable]]

    IGNORE_MISSING_TABLES = [
        "django_migrations",
    ]

    DIFF_TYPES = [
        'error',
        'comment',
        'table-missing-in-db',
        'table-missing-in-model',
        'field-missing-in-db',
        'field-missing-in-model',
        'fkey-missing-in-db',
        'fkey-missing-in-model',
        'index-missing-in-db',
        'index-missing-in-model',
        'unique-missing-in-db',
        'unique-missing-in-model',
        'field-type-differ',
        'field-parameter-differ',
        'notnull-differ',
    ]
    DIFF_TEXTS = {
        'error': 'error: %(0)s',
        'comment': 'comment: %(0)s',
        'table-missing-in-db': "table '%(0)s' missing in database",
        'table-missing-in-model': "table '%(0)s' missing in models",
        'field-missing-in-db': "field '%(1)s' defined in model but missing in database",
        'field-missing-in-model': "field '%(1)s' defined in database but missing in model",
        'fkey-missing-in-db': "field '%(1)s' FOREIGN KEY defined in model but missing in database",
        'fkey-missing-in-model': "field '%(1)s' FOREIGN KEY defined in database but missing in model",
        'index-missing-in-db': "field '%(1)s' INDEX defined in model but missing in database",
        'index-missing-in-model': "field '%(1)s' INDEX defined in database schema but missing in model",
        'unique-missing-in-db': "field '%(1)s' UNIQUE defined in model but missing in database",
        'unique-missing-in-model': "field '%(1)s' UNIQUE defined in database schema but missing in model",
        'field-type-differ': "field '%(1)s' not of same type: db='%(3)s', model='%(2)s'",
        'field-parameter-differ': "field '%(1)s' parameters differ: db='%(3)s', model='%(2)s'",
        'notnull-differ': "field '%(1)s' null constraint should be '%(2)s' in the database",
    }

    SQL_FIELD_MISSING_IN_DB = lambda self, style, qn, args: "%s %s\n\t%s %s %s;" % (style.SQL_KEYWORD('ALTER TABLE'), style.SQL_TABLE(qn(args[0])), style.SQL_KEYWORD('ADD COLUMN'), style.SQL_FIELD(qn(args[1])), ' '.join(style.SQL_COLTYPE(a) if i == 0 else style.SQL_KEYWORD(a) for i, a in enumerate(args[2:])))
    SQL_FIELD_MISSING_IN_MODEL = lambda self, style, qn, args: "%s %s\n\t%s %s;" % (style.SQL_KEYWORD('ALTER TABLE'), style.SQL_TABLE(qn(args[0])), style.SQL_KEYWORD('DROP COLUMN'), style.SQL_FIELD(qn(args[1])))
    SQL_FKEY_MISSING_IN_DB = lambda self, style, qn, args: "%s %s\n\t%s %s %s %s %s (%s)%s;" % (style.SQL_KEYWORD('ALTER TABLE'), style.SQL_TABLE(qn(args[0])), style.SQL_KEYWORD('ADD COLUMN'), style.SQL_FIELD(qn(args[1])), ' '.join(style.SQL_COLTYPE(a) if i == 0 else style.SQL_KEYWORD(a) for i, a in enumerate(args[4:])), style.SQL_KEYWORD('REFERENCES'), style.SQL_TABLE(qn(args[2])), style.SQL_FIELD(qn(args[3])), connection.ops.deferrable_sql())
    SQL_INDEX_MISSING_IN_DB = lambda self, style, qn, args: "%s %s\n\t%s %s (%s%s);" % (style.SQL_KEYWORD('CREATE INDEX'), style.SQL_TABLE(qn("%s" % '_'.join(a for a in args[0:3] if a))), style.SQL_KEYWORD('ON'), style.SQL_TABLE(qn(args[0])), style.SQL_FIELD(qn(args[1])), style.SQL_KEYWORD(args[3]))
    # FIXME: need to lookup index name instead of just appending _idx to table + fieldname
    SQL_INDEX_MISSING_IN_MODEL = lambda self, style, qn, args: "%s %s;" % (style.SQL_KEYWORD('DROP INDEX'), style.SQL_TABLE(qn("%s" % '_'.join(a for a in args[0:3] if a))))
    SQL_UNIQUE_MISSING_IN_DB = lambda self, style, qn, args: "%s %s\n\t%s %s (%s);" % (style.SQL_KEYWORD('ALTER TABLE'), style.SQL_TABLE(qn(args[0])), style.SQL_KEYWORD('ADD'), style.SQL_KEYWORD('UNIQUE'), style.SQL_FIELD(qn(args[1])))
    # FIXME: need to lookup unique constraint name instead of appending _key to table + fieldname
    SQL_UNIQUE_MISSING_IN_MODEL = lambda self, style, qn, args: "%s %s\n\t%s %s %s;" % (style.SQL_KEYWORD('ALTER TABLE'), style.SQL_TABLE(qn(args[0])), style.SQL_KEYWORD('DROP'), style.SQL_KEYWORD('CONSTRAINT'), style.SQL_TABLE(qn("%s_key" % ('_'.join(args[:2])))))
    SQL_FIELD_TYPE_DIFFER = lambda self, style, qn, args: "%s %s\n\t%s %s %s;" % (style.SQL_KEYWORD('ALTER TABLE'), style.SQL_TABLE(qn(args[0])), style.SQL_KEYWORD("MODIFY"), style.SQL_FIELD(qn(args[1])), style.SQL_COLTYPE(args[2]))
    SQL_FIELD_PARAMETER_DIFFER = lambda self, style, qn, args: "%s %s\n\t%s %s %s;" % (style.SQL_KEYWORD('ALTER TABLE'), style.SQL_TABLE(qn(args[0])), style.SQL_KEYWORD("MODIFY"), style.SQL_FIELD(qn(args[1])), style.SQL_COLTYPE(args[2]))
    SQL_NOTNULL_DIFFER = lambda self, style, qn, args: "%s %s\n\t%s %s %s %s;" % (style.SQL_KEYWORD('ALTER TABLE'), style.SQL_TABLE(qn(args[0])), style.SQL_KEYWORD('MODIFY'), style.SQL_FIELD(qn(args[1])), style.SQL_KEYWORD(args[2]), style.SQL_KEYWORD('NOT NULL'))
    SQL_ERROR = lambda self, style, qn, args: style.NOTICE('-- Error: %s' % style.ERROR(args[0]))
    SQL_COMMENT = lambda self, style, qn, args: style.NOTICE('-- Comment: %s' % style.SQL_TABLE(args[0]))
    SQL_TABLE_MISSING_IN_DB = lambda self, style, qn, args: style.NOTICE('-- Table missing: %s' % args[0])
    SQL_TABLE_MISSING_IN_MODEL = lambda self, style, qn, args: style.NOTICE('-- Model missing for table: %s' % args[0])

    can_detect_notnull_differ = False
    can_detect_unsigned_differ = False
    unsigned_suffix = None  # type: Optional[str]

    def __init__(self, app_models, options):
        self.has_differences = None
        self.app_models = app_models
        self.options = options
        self.dense = options['dense_output']

        self.introspection = connection.introspection

        self.cursor = connection.cursor()
        self.django_tables = self.introspection.django_table_names(only_existing=options['only_existing'])
        # TODO: We are losing information about tables which are views here
        self.db_tables = [table_info.name for table_info in self.introspection.get_table_list(self.cursor)]
        self.differences = []
        self.unknown_db_fields = {}
        self.new_db_fields = set()
        self.null = {}
        self.unsigned = set()

        self.DIFF_SQL = {
            'error': self.SQL_ERROR,
            'comment': self.SQL_COMMENT,
            'table-missing-in-db': self.SQL_TABLE_MISSING_IN_DB,
            'table-missing-in-model': self.SQL_TABLE_MISSING_IN_MODEL,
            'field-missing-in-db': self.SQL_FIELD_MISSING_IN_DB,
            'field-missing-in-model': self.SQL_FIELD_MISSING_IN_MODEL,
            'fkey-missing-in-db': self.SQL_FKEY_MISSING_IN_DB,
            'fkey-missing-in-model': self.SQL_FIELD_MISSING_IN_MODEL,
            'index-missing-in-db': self.SQL_INDEX_MISSING_IN_DB,
            'index-missing-in-model': self.SQL_INDEX_MISSING_IN_MODEL,
            'unique-missing-in-db': self.SQL_UNIQUE_MISSING_IN_DB,
            'unique-missing-in-model': self.SQL_UNIQUE_MISSING_IN_MODEL,
            'field-type-differ': self.SQL_FIELD_TYPE_DIFFER,
            'field-parameter-differ': self.SQL_FIELD_PARAMETER_DIFFER,
            'notnull-differ': self.SQL_NOTNULL_DIFFER,
        }

        if self.can_detect_notnull_differ:
            self.load_null()

        if self.can_detect_unsigned_differ:
            self.load_unsigned()

    def load_null(self):
        raise NotImplementedError("load_null functions must be implemented if diff backend has 'can_detect_notnull_differ' set to True")

    def load_unsigned(self):
        raise NotImplementedError("load_unsigned function must be implemented if diff backend has 'can_detect_unsigned_differ' set to True")

    def add_app_model_marker(self, app_label, model_name):
        self.differences.append((app_label, model_name, []))

    def add_difference(self, diff_type, *args):
        assert diff_type in self.DIFF_TYPES, 'Unknown difference type'
        self.differences[-1][-1].append((diff_type, args))

    def get_data_types_reverse_override(self):
        # type: () -> Dict[int, Union[str, Callable]]
        return self.DATA_TYPES_REVERSE_OVERRIDE

    def sql_to_dict(self, query, param):
        """ sql_to_dict(query, param) -> list of dicts

        code from snippet at http://www.djangosnippets.org/snippets/1383/
        """
        cursor = connection.cursor()
        cursor.execute(query, param)
        fieldnames = [name[0] for name in cursor.description]
        result = []
        for row in cursor.fetchall():
            rowset = []
            for field in zip(fieldnames, row):
                rowset.append(field)
            result.append(dict(rowset))
        return result

    def get_field_model_type(self, field):
        return field.db_type(connection=connection)

    def get_field_db_type_kwargs(self, current_kwargs, description, field=None, table_name=None, reverse_type=None):
        return {}

    def get_field_db_type(self, description, field=None, table_name=None):
        # DB-API cursor.description
        # (name, type_code, display_size, internal_size, precision, scale, null_ok) = description
        type_code = description[1]
        DATA_TYPES_REVERSE_OVERRIDE = self.get_data_types_reverse_override()
        if type_code in DATA_TYPES_REVERSE_OVERRIDE:
            reverse_type = DATA_TYPES_REVERSE_OVERRIDE[type_code]
        else:
            try:
                reverse_type = self.introspection.get_field_type(type_code, description)
            except KeyError:
                reverse_type = self.get_field_db_type_lookup(type_code)
                if not reverse_type:
                    # type_code not found in data_types_reverse map
                    key = (self.differences[-1][:2], description[:2])
                    if key not in self.unknown_db_fields:
                        self.unknown_db_fields[key] = 1
                        self.add_difference('comment', "Unknown database type for field '%s' (%s)" % (description[0], type_code))
                    return None

        if callable(reverse_type):
            reverse_type = reverse_type()

        kwargs = {}

        if isinstance(reverse_type, dict):
            kwargs.update(reverse_type['kwargs'])
            reverse_type = reverse_type['name']

        if type_code == 16946 and field and getattr(field, 'geom_type', None) == 'POINT':
            reverse_type = 'django.contrib.gis.db.models.fields.PointField'

        if isinstance(reverse_type, tuple):
            kwargs.update(reverse_type[1])
            reverse_type = reverse_type[0]

        if reverse_type == "CharField" and description[3]:
            kwargs['max_length'] = description[3]

        if reverse_type == "DecimalField":
            kwargs['max_digits'] = description[4]
            kwargs['decimal_places'] = description[5] and abs(description[5]) or description[5]

        if description[6]:
            kwargs['blank'] = True
            if reverse_type not in ('TextField', 'CharField'):
                kwargs['null'] = True

        if field and getattr(field, 'geography', False):
            kwargs['geography'] = True

        if reverse_type == 'GeometryField':
            geo_col = description[0]
            # Getting a more specific field type and any additional parameters
            # from the `get_geometry_type` routine for the spatial backend.
            reverse_type, geo_params = self.introspection.get_geometry_type(table_name, geo_col)
            if geo_params:
                kwargs.update(geo_params)
            reverse_type = 'django.contrib.gis.db.models.fields.%s' % reverse_type

        extra_kwargs = self.get_field_db_type_kwargs(kwargs, description, field, table_name, reverse_type)
        kwargs.update(extra_kwargs)

        field_class = self.get_field_class(reverse_type)
        field_db_type = field_class(**kwargs).db_type(connection=connection)

        tablespace = field.db_tablespace
        if not tablespace:
            tablespace = "public"
        if (tablespace, table_name, field.column) in self.unsigned:
            field_db_type = '%s %s' % (field_db_type, self.unsigned_suffix)

        return field_db_type

    def get_field_db_type_lookup(self, type_code):
        return None

    def get_field_class(self, class_path):
        if '.' in class_path:
            module_path, package_name = class_path.rsplit('.', 1)
            module = importlib.import_module(module_path)
            return getattr(module, package_name)
        else:
            return getattr(models, class_path)

    def get_field_db_nullable(self, field, table_name):
        tablespace = field.db_tablespace
        if tablespace == "":
            tablespace = "public"
        attname = field.db_column or field.attname
        return self.null.get((tablespace, table_name, attname), 'fixme')

    def strip_parameters(self, field_type):
        if field_type and field_type != 'double precision':
            return field_type.split(" ")[0].split("(")[0].lower()
        return field_type

    def find_unique_missing_in_db(self, meta, table_indexes, table_constraints, table_name):
        for field in all_local_fields(meta):
            if field.unique and meta.managed:
                attname = field.db_column or field.attname
                db_field_unique = table_indexes.get(attname, {}).get('unique')
                if not db_field_unique and table_constraints:
                    db_field_unique = any(constraint['unique'] for contraint_name, constraint in six.iteritems(table_constraints) if [attname] == constraint['columns'])
                if attname in table_indexes and db_field_unique:
                    continue
                self.add_difference('unique-missing-in-db', table_name, attname)

    def find_unique_missing_in_model(self, meta, table_indexes, table_constraints, table_name):
        # TODO: Postgresql does not list unique_togethers in table_indexes
        #       MySQL does
        fields = dict([(field.db_column or field.name, field.unique) for field in all_local_fields(meta)])
        for att_name, att_opts in six.iteritems(table_indexes):
            db_field_unique = att_opts['unique']
            if not db_field_unique and table_constraints:
                db_field_unique = any(constraint['unique'] for contraint_name, constraint in six.iteritems(table_constraints) if att_name in constraint['columns'])
            if db_field_unique and att_name in fields and not fields[att_name]:
                if att_name in flatten(meta.unique_together):
                    continue
                self.add_difference('unique-missing-in-model', table_name, att_name)

    def find_index_missing_in_db(self, meta, table_indexes, table_constraints, table_name):
        for field in all_local_fields(meta):
            if field.db_index:
                attname = field.db_column or field.attname
                if attname not in table_indexes:
                    self.add_difference('index-missing-in-db', table_name, attname, '', '')
                    db_type = field.db_type(connection=connection)
                    if db_type.startswith('varchar'):
                        self.add_difference('index-missing-in-db', table_name, attname, 'like', ' varchar_pattern_ops')
                    if db_type.startswith('text'):
                        self.add_difference('index-missing-in-db', table_name, attname, 'like', ' text_pattern_ops')

    def find_index_missing_in_model(self, meta, table_indexes, table_constraints, table_name):
        fields = dict([(field.name, field) for field in all_local_fields(meta)])
        for att_name, att_opts in six.iteritems(table_indexes):
            if att_name in fields:
                field = fields[att_name]
                db_field_unique = att_opts['unique']
                if not db_field_unique and table_constraints:
                    db_field_unique = any(constraint['unique'] for contraint_name, constraint in six.iteritems(table_constraints) if att_name in constraint['columns'])
                if field.db_index:
                    continue
                if getattr(field, 'spatial_index', False):
                    continue
                if att_opts['primary_key'] and field.primary_key:
                    continue
                if db_field_unique and field.unique:
                    continue
                if db_field_unique and att_name in flatten(meta.unique_together):
                    continue
                self.add_difference('index-missing-in-model', table_name, att_name)
                db_type = field.db_type(connection=connection)
                if db_type.startswith('varchar') or db_type.startswith('text'):
                    self.add_difference('index-missing-in-model', table_name, att_name, 'like')

    def find_field_missing_in_model(self, fieldmap, table_description, table_name):
        for row in table_description:
            if row[0] not in fieldmap:
                self.add_difference('field-missing-in-model', table_name, row[0])

    def find_field_missing_in_db(self, fieldmap, table_description, table_name):
        db_fields = [row[0] for row in table_description]
        for field_name, field in six.iteritems(fieldmap):
            if field_name not in db_fields:
                field_output = []

                if field.remote_field:
                    field_output.extend([field.remote_field.model._meta.db_table, field.remote_field.model._meta.get_field(field.remote_field.field_name).column])
                    op = 'fkey-missing-in-db'
                else:
                    op = 'field-missing-in-db'
                field_output.append(field.db_type(connection=connection))
                if self.options['include_defaults'] and field.has_default():
                    field_output.append('DEFAULT %s' % field.get_prep_value(field.get_default()))
                if not field.null:
                    field_output.append('NOT NULL')
                self.add_difference(op, table_name, field_name, *field_output)
                self.new_db_fields.add((table_name, field_name))

    def find_field_type_differ(self, meta, table_description, table_name, func=None):
        db_fields = dict([(row[0], row) for row in table_description])
        for field in all_local_fields(meta):
            if field.name not in db_fields:
                continue
            description = db_fields[field.name]

            model_type = self.get_field_model_type(field)
            db_type = self.get_field_db_type(description, field, table_name)

            # use callback function if defined
            if func:
                model_type, db_type = func(field, description, model_type, db_type)

            if not self.strip_parameters(db_type) == self.strip_parameters(model_type):
                self.add_difference('field-type-differ', table_name, field.name, model_type, db_type)

    def find_field_parameter_differ(self, meta, table_description, table_name, func=None):
        db_fields = dict([(row[0], row) for row in table_description])
        for field in all_local_fields(meta):
            if field.name not in db_fields:
                continue
            description = db_fields[field.name]

            model_type = self.get_field_model_type(field)
            db_type = self.get_field_db_type(description, field, table_name)

            if not self.strip_parameters(model_type) == self.strip_parameters(db_type):
                continue

            # use callback function if defined
            if func:
                model_type, db_type = func(field, description, model_type, db_type)

            model_check = field.db_parameters(connection=connection)['check']
            if ' CHECK' in db_type:
                db_type, db_check = db_type.split(" CHECK", 1)
                db_check = db_check.strip().lstrip("(").rstrip(")")
            else:
                db_check = None

            if not model_type == db_type or not model_check == db_check:
                self.add_difference('field-parameter-differ', table_name, field.name, model_type, db_type)

    def find_field_notnull_differ(self, meta, table_description, table_name):
        if not self.can_detect_notnull_differ:
            return

        for field in all_local_fields(meta):
            attname = field.db_column or field.attname
            if (table_name, attname) in self.new_db_fields:
                continue
            null = self.get_field_db_nullable(field, table_name)
            if field.null != null:
                action = field.null and 'DROP' or 'SET'
                self.add_difference('notnull-differ', table_name, attname, action)

    def get_constraints(self, cursor, table_name, introspection):
        return {}

    def find_differences(self):
        if self.options['all_applications']:
            self.add_app_model_marker(None, None)
            for table in self.db_tables:
                if table not in self.django_tables and table not in self.IGNORE_MISSING_TABLES:
                    self.add_difference('table-missing-in-model', table)

        cur_app_label = None
        for app_model in self.app_models:
            meta = app_model._meta
            table_name = meta.db_table
            app_label = meta.app_label

            if not self.options['include_proxy_models'] and meta.proxy:
                continue

            if cur_app_label != app_label:
                # Marker indicating start of difference scan for this table_name
                self.add_app_model_marker(app_label, app_model.__name__)

            if table_name not in self.db_tables:
                # Table is missing from database
                self.add_difference('table-missing-in-db', table_name)
                continue

            if hasattr(self.introspection, 'get_constraints'):
                table_constraints = self.introspection.get_constraints(self.cursor, table_name)
            else:
                table_constraints = self.get_constraints(self.cursor, table_name, self.introspection)

            fieldmap = dict([(field.db_column or field.get_attname(), field) for field in all_local_fields(meta)])

            # add ordering field if model uses order_with_respect_to
            if meta.order_with_respect_to:
                fieldmap['_order'] = ORDERING_FIELD

            try:
                table_description = self.introspection.get_table_description(self.cursor, table_name)
            except Exception as e:
                self.add_difference('error', 'unable to introspect table: %s' % str(e).strip())
                transaction.rollback()  # reset transaction
                continue

            # map table_contraints into table_indexes
            table_indexes = {}
            for _, dct in table_constraints.items():
                columns = dct['columns']
                if len(columns) == 1:
                    table_indexes[columns[0]] = {
                        'primary_key': dct['primary_key'],
                        'unique': dct['unique'],
                    }

            # Fields which are defined in database but not in model
            # 1) find: 'unique-missing-in-model'
            self.find_unique_missing_in_model(meta, table_indexes, table_constraints, table_name)
            # 2) find: 'index-missing-in-model'
            self.find_index_missing_in_model(meta, table_indexes, table_constraints, table_name)
            # 3) find: 'field-missing-in-model'
            self.find_field_missing_in_model(fieldmap, table_description, table_name)

            # Fields which are defined in models but not in database
            # 4) find: 'field-missing-in-db'
            self.find_field_missing_in_db(fieldmap, table_description, table_name)
            # 5) find: 'unique-missing-in-db'
            self.find_unique_missing_in_db(meta, table_indexes, table_constraints, table_name)
            # 6) find: 'index-missing-in-db'
            self.find_index_missing_in_db(meta, table_indexes, table_constraints, table_name)

            # Fields which have a different type or parameters
            # 7) find: 'type-differs'
            self.find_field_type_differ(meta, table_description, table_name)
            # 8) find: 'type-parameter-differs'
            self.find_field_parameter_differ(meta, table_description, table_name)
            # 9) find: 'field-notnull'
            self.find_field_notnull_differ(meta, table_description, table_name)
        self.has_differences = max([len(diffs) for _app_label, _model_name, diffs in self.differences])

    def print_diff(self, style=no_style()):
        """ print differences to stdout """
        if self.options['sql']:
            self.print_diff_sql(style)
        else:
            self.print_diff_text(style)

    def print_diff_text(self, style):
        if not self.can_detect_notnull_differ:
            print(style.NOTICE("# Detecting notnull changes not implemented for this database backend"))
            print("")

        if not self.can_detect_unsigned_differ:
            print(style.NOTICE("# Detecting unsigned changes not implemented for this database backend"))
            print("")

        cur_app_label = None
        for app_label, model_name, diffs in self.differences:
            if not diffs:
                continue
            if not self.dense and app_label and cur_app_label != app_label:
                print("%s %s" % (style.NOTICE("+ Application:"), style.SQL_TABLE(app_label)))
                cur_app_label = app_label
            if not self.dense and model_name:
                print("%s %s" % (style.NOTICE("|-+ Differences for model:"), style.SQL_TABLE(model_name)))
            for diff in diffs:
                diff_type, diff_args = diff
                text = self.DIFF_TEXTS[diff_type] % dict((str(i), style.SQL_TABLE(e)) for i, e in enumerate(diff_args))
                text = "'".join(i % 2 == 0 and style.ERROR(e) or e for i, e in enumerate(text.split("'")))
                if not self.dense:
                    print("%s %s" % (style.NOTICE("|--+"), text))
                else:
                    if app_label:
                        print("%s %s %s %s %s" % (style.NOTICE("App"), style.SQL_TABLE(app_label), style.NOTICE('Model'), style.SQL_TABLE(model_name), text))
                    else:
                        print(text)

    def print_diff_sql(self, style):
        if not self.can_detect_notnull_differ:
            print(style.NOTICE("-- Detecting notnull changes not implemented for this database backend"))
            print("")

        cur_app_label = None
        qn = connection.ops.quote_name
        if not self.has_differences:
            if not self.dense:
                print(style.SQL_KEYWORD("-- No differences"))
        else:
            print(style.SQL_KEYWORD("BEGIN;"))
            for app_label, model_name, diffs in self.differences:
                if not diffs:
                    continue
                if not self.dense and cur_app_label != app_label:
                    print(style.NOTICE("-- Application: %s" % style.SQL_TABLE(app_label)))
                    cur_app_label = app_label
                if not self.dense and model_name:
                    print(style.NOTICE("-- Model: %s" % style.SQL_TABLE(model_name)))
                for diff in diffs:
                    diff_type, diff_args = diff
                    text = self.DIFF_SQL[diff_type](style, qn, diff_args)
                    if self.dense:
                        text = text.replace("\n\t", " ")
                    print(text)
            print(style.SQL_KEYWORD("COMMIT;"))


class GenericSQLDiff(SQLDiff):
    can_detect_notnull_differ = False


class MySQLDiff(SQLDiff):
    can_detect_notnull_differ = True
    can_detect_unsigned_differ = True
    unsigned_suffix = 'UNSIGNED'

    def __init__(self, app_models, options):
        super(MySQLDiff, self).__init__(app_models, options)
        self.auto_increment = set()
        self.load_auto_increment()

    def load_null(self):
        tablespace = 'public'
        for table_name in self.db_tables:
            result = self.sql_to_dict("""
                SELECT column_name, is_nullable
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                    AND table_name = %s""", [table_name])
            for table_info in result:
                key = (tablespace, table_name, table_info['column_name'])
                self.null[key] = table_info['is_nullable'] == 'YES'

    def load_unsigned(self):
        tablespace = 'public'
        for table_name in self.db_tables:
            result = self.sql_to_dict("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                    AND table_name = %s
                    AND column_type LIKE '%%unsigned'""", [table_name])
            for table_info in result:
                key = (tablespace, table_name, table_info['column_name'])
                self.unsigned.add(key)

    def load_auto_increment(self):
        for table_name in self.db_tables:
            result = self.sql_to_dict("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = DATABASE()
                   AND table_name = %s
                   AND extra = 'auto_increment'""", [table_name])
            for table_info in result:
                key = (table_name, table_info['column_name'])
                self.auto_increment.add(key)

    # All the MySQL hacks together create something of a problem
    # Fixing one bug in MySQL creates another issue. So just keep in mind
    # that this is way unreliable for MySQL atm.
    def get_field_db_type(self, description, field=None, table_name=None):
        from MySQLdb.constants import FIELD_TYPE
        db_type = super(MySQLDiff, self).get_field_db_type(description, field, table_name)
        if not db_type:
            return
        if field:
            # MySQL isn't really sure about char's and varchar's like sqlite
            field_type = self.get_field_model_type(field)
            # Fix char/varchar inconsistencies
            if self.strip_parameters(field_type) == 'char' and self.strip_parameters(db_type) == 'varchar':
                db_type = db_type.lstrip("var")
            # They like to call 'bool's 'tinyint(1)' and introspection makes that a integer
            # just convert it back to it's proper type, a bool is a bool and nothing else.
            if db_type == 'integer' and description[1] == FIELD_TYPE.TINY and description[2] == 1:
                db_type = 'bool'
            if (table_name, field.column) in self.auto_increment:
                db_type += ' AUTO_INCREMENT'
        return db_type


class SqliteSQLDiff(SQLDiff):
    can_detect_notnull_differ = True

    def load_null(self):
        for table_name in self.db_tables:
            # sqlite does not support tablespaces
            tablespace = "public"
            # index, column_name, column_type, nullable, default_value
            # see: http://www.sqlite.org/pragma.html#pragma_table_info
            for table_info in self.sql_to_dict("PRAGMA table_info('%s');" % table_name, []):
                key = (tablespace, table_name, table_info['name'])
                self.null[key] = not table_info['notnull']

    # Unique does not seem to be implied on Sqlite for Primary_key's
    # if this is more generic among databases this might be usefull
    # to add to the superclass's find_unique_missing_in_db method
    def find_unique_missing_in_db(self, meta, table_indexes, table_constraints, table_name):
        for field in all_local_fields(meta):
            if field.unique:
                attname = field.db_column or field.attname
                if attname in table_indexes and table_indexes[attname]['unique']:
                    continue
                if attname in table_indexes and table_indexes[attname]['primary_key']:
                    continue
                self.add_difference('unique-missing-in-db', table_name, attname)

    # Finding Indexes by using the get_indexes dictionary doesn't seem to work
    # for sqlite.
    def find_index_missing_in_db(self, meta, table_indexes, table_constraints, table_name):
        pass

    def find_index_missing_in_model(self, meta, table_indexes, table_constraints, table_name):
        pass

    def get_field_db_type(self, description, field=None, table_name=None):
        db_type = super(SqliteSQLDiff, self).get_field_db_type(description, field, table_name)
        if not db_type:
            return
        if field:
            field_type = self.get_field_model_type(field)
            # Fix char/varchar inconsistencies
            if self.strip_parameters(field_type) == 'char' and self.strip_parameters(db_type) == 'varchar':
                db_type = db_type.lstrip("var")
        return db_type


class PostgresqlSQLDiff(SQLDiff):
    can_detect_notnull_differ = True
    can_detect_unsigned_differ = True

    DATA_TYPES_REVERSE_NAME = {
        'hstore': 'django_hstore.hstore.DictionaryField',
    }

    # Hopefully in the future we can add constraint checking and other more
    # advanced checks based on this database.
    SQL_LOAD_CONSTRAINTS = """
    SELECT nspname, relname, conname, attname, pg_get_constraintdef(pg_constraint.oid)
    FROM pg_constraint
    INNER JOIN pg_attribute ON pg_constraint.conrelid = pg_attribute.attrelid AND pg_attribute.attnum = any(pg_constraint.conkey)
    INNER JOIN pg_class ON conrelid=pg_class.oid
    INNER JOIN pg_namespace ON pg_namespace.oid=pg_class.relnamespace
    ORDER BY CASE WHEN contype='f' THEN 0 ELSE 1 END,contype,nspname,relname,conname;
    """
    SQL_LOAD_NULL = """
    SELECT nspname, relname, attname, attnotnull
    FROM pg_attribute
    INNER JOIN pg_class ON attrelid=pg_class.oid
    INNER JOIN pg_namespace ON pg_namespace.oid=pg_class.relnamespace;
    """

    SQL_FIELD_TYPE_DIFFER = lambda self, style, qn, args: "%s %s\n\t%s %s %s %s;" % (style.SQL_KEYWORD('ALTER TABLE'), style.SQL_TABLE(qn(args[0])), style.SQL_KEYWORD('ALTER'), style.SQL_FIELD(qn(args[1])), style.SQL_KEYWORD("TYPE"), style.SQL_COLTYPE(args[2]))
    SQL_FIELD_PARAMETER_DIFFER = lambda self, style, qn, args: "%s %s\n\t%s %s %s %s;" % (style.SQL_KEYWORD('ALTER TABLE'), style.SQL_TABLE(qn(args[0])), style.SQL_KEYWORD('ALTER'), style.SQL_FIELD(qn(args[1])), style.SQL_KEYWORD("TYPE"), style.SQL_COLTYPE(args[2]))
    SQL_NOTNULL_DIFFER = lambda self, style, qn, args: "%s %s\n\t%s %s %s %s;" % (style.SQL_KEYWORD('ALTER TABLE'), style.SQL_TABLE(qn(args[0])), style.SQL_KEYWORD('ALTER COLUMN'), style.SQL_FIELD(qn(args[1])), style.SQL_KEYWORD(args[2]), style.SQL_KEYWORD('NOT NULL'))

    def __init__(self, app_models, options):
        super(PostgresqlSQLDiff, self).__init__(app_models, options)
        self.check_constraints = {}
        self.load_constraints()

    def load_null(self):
        for dct in self.sql_to_dict(self.SQL_LOAD_NULL, []):
            key = (dct['nspname'], dct['relname'], dct['attname'])
            self.null[key] = not dct['attnotnull']

    def load_unsigned(self):
        # PostgreSQL does not support unsigned, so no columns are
        # unsigned. Nothing to do.
        pass

    def load_constraints(self):
        for dct in self.sql_to_dict(self.SQL_LOAD_CONSTRAINTS, []):
            key = (dct['nspname'], dct['relname'], dct['attname'])
            if 'CHECK' in dct['pg_get_constraintdef']:
                self.check_constraints[key] = dct

    def get_data_type_arrayfield(self, base_field):
        return {
            'name': 'django.contrib.postgres.fields.ArrayField',
            'kwargs': {
                'base_field': self.get_field_class(base_field)(),
            },
        }

    def get_data_types_reverse_override(self):
        return {
            1042: 'CharField',
            1000: lambda: self.get_data_type_arrayfield(base_field='BooleanField'),
            1001: lambda: self.get_data_type_arrayfield(base_field='BinaryField'),
            1002: lambda: self.get_data_type_arrayfield(base_field='CharField'),
            1005: lambda: self.get_data_type_arrayfield(base_field='IntegerField'),
            1006: lambda: self.get_data_type_arrayfield(base_field='IntegerField'),
            1007: lambda: self.get_data_type_arrayfield(base_field='IntegerField'),
            1009: lambda: self.get_data_type_arrayfield(base_field='CharField'),
            1014: lambda: self.get_data_type_arrayfield(base_field='CharField'),
            1015: lambda: self.get_data_type_arrayfield(base_field='CharField'),
            1016: lambda: self.get_data_type_arrayfield(base_field='BigIntegerField'),
            1017: lambda: self.get_data_type_arrayfield(base_field='FloatField'),
            1021: lambda: self.get_data_type_arrayfield(base_field='FloatField'),
            1022: lambda: self.get_data_type_arrayfield(base_field='FloatField'),
            1115: lambda: self.get_data_type_arrayfield(base_field='DateTimeField'),
            1185: lambda: self.get_data_type_arrayfield(base_field='DateTimeField'),
            1231: lambda: self.get_data_type_arrayfield(base_field='DecimalField'),
            # {'name': 'django.contrib.postgres.fields.ArrayField', 'kwargs': {'base_field': 'IntegerField'}},
            1186: lambda: self.get_data_type_arrayfield(base_field='DurationField'),
            # 1186: 'django.db.models.fields.DurationField',
            3614: 'django.contrib.postgres.search.SearchVectorField',
            3802: 'django.contrib.postgres.fields.JSONField',
        }

    def get_constraints(self, cursor, table_name, introspection):
        """ backport of django's introspection.get_constraints(...) """
        constraints = {}
        # Loop over the key table, collecting things as constraints
        # This will get PKs, FKs, and uniques, but not CHECK
        cursor.execute("""
            SELECT
                kc.constraint_name,
                kc.column_name,
                c.constraint_type,
                array(SELECT table_name::text || '.' || column_name::text FROM information_schema.constraint_column_usage WHERE constraint_name = kc.constraint_name)
            FROM information_schema.key_column_usage AS kc
            JOIN information_schema.table_constraints AS c ON
                kc.table_schema = c.table_schema AND
                kc.table_name = c.table_name AND
                kc.constraint_name = c.constraint_name
            WHERE
                kc.table_schema = %s AND
                kc.table_name = %s
        """, ["public", table_name])
        for constraint, column, kind, used_cols in cursor.fetchall():
            # If we're the first column, make the record
            if constraint not in constraints:
                constraints[constraint] = {
                    "columns": [],
                    "primary_key": kind.lower() == "primary key",
                    "unique": kind.lower() in ["primary key", "unique"],
                    "foreign_key": tuple(used_cols[0].split(".", 1)) if kind.lower() == "foreign key" else None,
                    "check": False,
                    "index": False,
                }
            # Record the details
            constraints[constraint]['columns'].append(column)
        # Now get CHECK constraint columns
        cursor.execute("""
            SELECT kc.constraint_name, kc.column_name
            FROM information_schema.constraint_column_usage AS kc
            JOIN information_schema.table_constraints AS c ON
                kc.table_schema = c.table_schema AND
                kc.table_name = c.table_name AND
                kc.constraint_name = c.constraint_name
            WHERE
                c.constraint_type = 'CHECK' AND
                kc.table_schema = %s AND
                kc.table_name = %s
        """, ["public", table_name])
        for constraint, column in cursor.fetchall():
            # If we're the first column, make the record
            if constraint not in constraints:
                constraints[constraint] = {
                    "columns": [],
                    "primary_key": False,
                    "unique": False,
                    "foreign_key": None,
                    "check": True,
                    "index": False,
                }
            # Record the details
            constraints[constraint]['columns'].append(column)
        # Now get indexes
        cursor.execute("""
            SELECT
                c2.relname,
                ARRAY(
                    SELECT (SELECT attname FROM pg_catalog.pg_attribute WHERE attnum = i AND attrelid = c.oid)
                    FROM unnest(idx.indkey) i
                ),
                idx.indisunique,
                idx.indisprimary
            FROM pg_catalog.pg_class c, pg_catalog.pg_class c2,
                pg_catalog.pg_index idx
            WHERE c.oid = idx.indrelid
                AND idx.indexrelid = c2.oid
                AND c.relname = %s
        """, [table_name])
        for index, columns, unique, primary in cursor.fetchall():
            if index not in constraints:
                constraints[index] = {
                    "columns": list(columns),
                    "primary_key": primary,
                    "unique": unique,
                    "foreign_key": None,
                    "check": False,
                    "index": True,
                }
        return constraints

    # def get_field_db_type_kwargs(self, current_kwargs, description, field=None, table_name=None, reverse_type=None):
    #     kwargs = {}
    #     if field and 'base_field' in current_kwargs:
    #         # find
    #         attname = field.db_column or field.attname
    #         introspect_db_type = self.sql_to_dict(
    #             """SELECT attname, format_type(atttypid, atttypmod) AS type
    #                 FROM   pg_attribute
    #                 WHERE  attrelid = %s::regclass
    #                 AND    attname = %s
    #                 AND    attnum > 0
    #                 AND    NOT attisdropped
    #                 ORDER  BY attnum;
    #             """,
    #             (table_name, attname)
    #         )[0]['type']
    #         # TODO: this gives the concrete type that the database uses, why not use this
    #         #       much earlier in the process to compare to whatever django spits out as
    #         #       the database type ?
    #         max_length = re.search("character varying\((\d+)\)\[\]", introspect_db_type)
    #         if max_length:
    #             kwargs['max_length'] = max_length[1]
    #     return kwargs

    def get_field_db_type(self, description, field=None, table_name=None):
        db_type = super(PostgresqlSQLDiff, self).get_field_db_type(description, field, table_name)
        if not db_type:
            return
        if field:
            if db_type.endswith("[]"):
                # TODO: This is a hack for array types. Ideally we either pass the correct
                #       constraints for the type in `get_data_type_arrayfield` which instantiates
                #       the array base_field or maybe even better restructure sqldiff entirely
                #       to be based around the concrete type yielded by the code below. That gives
                #       the complete type the database uses, why not use thie much earlier in the
                #       process to compare to whatever django spits out as the desired database type ?
                attname = field.db_column or field.attname
                introspect_db_type = self.sql_to_dict(
                    """SELECT attname, format_type(atttypid, atttypmod) AS type
                        FROM   pg_attribute
                        WHERE  attrelid = %s::regclass
                        AND    attname = %s
                        AND    attnum > 0
                        AND    NOT attisdropped
                        ORDER  BY attnum;
                    """,
                    (table_name, attname)
                )[0]['type']
                if introspect_db_type.startswith("character varying"):
                    introspect_db_type = introspect_db_type.replace("character varying", "varchar")

                return introspect_db_type

            if field.primary_key and isinstance(field, AutoField):
                if db_type == 'integer':
                    db_type = 'serial'
                elif db_type == 'bigint':
                    db_type = 'bigserial'
            if table_name:
                tablespace = field.db_tablespace
                if tablespace == "":
                    tablespace = "public"
                attname = field.db_column or field.attname
                check_constraint = self.check_constraints.get((tablespace, table_name, attname), {}).get('pg_get_constraintdef', None)
                if check_constraint:
                    check_constraint = check_constraint.replace("((", "(")
                    check_constraint = check_constraint.replace("))", ")")
                    check_constraint = '("'.join([')' in e and '" '.join(p.strip('"') for p in e.split(" ", 1)) or e for e in check_constraint.split("(")])
                    # TODO: might be more then one constraint in definition ?
                    db_type += ' ' + check_constraint
        return db_type

    def get_field_db_type_lookup(self, type_code):
        try:
            name = self.sql_to_dict("SELECT typname FROM pg_type WHERE typelem=%s;", [type_code])[0]['typname']
            return self.DATA_TYPES_REVERSE_NAME.get(name.strip('_'))
        except (IndexError, KeyError):
            pass

    """
    def find_field_type_differ(self, meta, table_description, table_name):
        def callback(field, description, model_type, db_type):
            if field.primary_key and db_type=='integer':
                db_type = 'serial'
            return model_type, db_type
        super(PostgresqlSQLDiff, self).find_field_type_differ(meta, table_description, table_name, callback)
    """


DATABASE_SQLDIFF_CLASSES = {
    'postgis': PostgresqlSQLDiff,
    'postgresql_psycopg2': PostgresqlSQLDiff,
    'postgresql': PostgresqlSQLDiff,
    'mysql': MySQLDiff,
    'sqlite3': SqliteSQLDiff,
    'oracle': GenericSQLDiff
}


class Command(BaseCommand):
    help = """Prints the (approximated) difference between models and fields in the database for the given app name(s).

It indicates how columns in the database are different from the sql that would
be generated by Django. This command is not a database migration tool. (Though
it can certainly help) It's purpose is to show the current differences as a way
to check/debug ur models compared to the real database tables and columns."""

    output_transaction = False

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('app_label', nargs='*')
        parser.add_argument(
            '--all-applications', '-a', action='store_true',
            default=False,
            dest='all_applications',
            help="Automaticly include all application from INSTALLED_APPS."
        )
        parser.add_argument(
            '--not-only-existing', '-e', action='store_false',
            default=True,
            dest='only_existing',
            help="Check all tables that exist in the database, not only tables that should exist based on models."
        )
        parser.add_argument(
            '--dense-output', '-d', action='store_true', dest='dense_output',
            default=False,
            help="Shows the output in dense format, normally output is spreaded over multiple lines."
        )
        parser.add_argument(
            '--output_text', '-t', action='store_false', dest='sql',
            default=True,
            help="Outputs the differences as descriptive text instead of SQL"
        )
        parser.add_argument(
            '--include-proxy-models', action='store_true', dest='include_proxy_models',
            default=False,
            help="Include proxy models in the graph"
        )
        parser.add_argument(
            '--include-defaults', action='store_true', dest='include_defaults',
            default=False,
            help="Include default values in SQL output (beta feature)"
        )
        parser.add_argument(
            '--migrate-for-tests', action='store_true', dest='migrate_for_tests',
            default=False,
            help=argparse.SUPPRESS
        )

    def __init__(self, *args, **kwargs):
        super(Command, self).__init__(*args, **kwargs)
        self.exit_code = 1

    @signalcommand
    def handle(self, *args, **options):
        from django.conf import settings
        from django.core.management import call_command

        app_labels = options['app_label']
        engine = None
        if hasattr(settings, 'DATABASES'):
            engine = settings.DATABASES['default']['ENGINE']
        else:
            engine = settings.DATABASE_ENGINE

        if engine == 'dummy':
            # This must be the "dummy" database backend, which means the user
            # hasn't set DATABASE_ENGINE.
            raise CommandError("""Django doesn't know which syntax to use for your SQL statements,
because you haven't specified the DATABASE_ENGINE setting.
Edit your settings file and change DATABASE_ENGINE to something like 'postgresql' or 'mysql'.""")

        if options['all_applications']:
            app_models = apps.get_models(include_auto_created=True)
        else:
            if not app_labels:
                raise CommandError('Enter at least one appname.')

            if not isinstance(app_labels, (list, tuple, set)):
                app_labels = [app_labels]

            app_models = []
            for app_label in app_labels:
                app_config = apps.get_app_config(app_label)
                app_models.extend(app_config.get_models(include_auto_created=True))

        if not app_models:
            raise CommandError('Unable to execute sqldiff no models founds.')

        migrate_for_tests = options['migrate_for_tests']
        if migrate_for_tests:
            call_command("migrate", *app_labels, no_input=True, run_syncdb=True)

        if not engine:
            engine = connection.__module__.split('.')[-2]

        if '.' in engine:
            engine = engine.split('.')[-1]

        cls = DATABASE_SQLDIFF_CLASSES.get(engine, GenericSQLDiff)
        sqldiff_instance = cls(app_models, options)
        sqldiff_instance.find_differences()
        if not sqldiff_instance.has_differences:
            self.exit_code = 0
        sqldiff_instance.print_diff(self.style)

    def execute(self, *args, **options):
        try:
            super(Command, self).execute(*args, **options)
        except CommandError as e:
            if options['traceback']:
                raise

            # self.stderr is not guaranteed to be set here
            stderr = getattr(self, 'stderr', None)
            if not stderr:
                stderr = OutputWrapper(sys.stderr, self.style.ERROR)
            stderr.write('%s: %s' % (e.__class__.__name__, e))
            sys.exit(2)

    def run_from_argv(self, argv):
        super(Command, self).run_from_argv(argv)
        sys.exit(self.exit_code)
