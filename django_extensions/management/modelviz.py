# -*- coding: utf-8 -*-
"""
modelviz.py - DOT file generator for Django Models

Based on:
  Django model to DOT (Graphviz) converter
  by Antonio Cavedoni <antonio@cavedoni.org>
  Adapted to be used with django-extensions
"""

import datetime
import os
import re

import six
from django.apps import apps
from django.db.models.fields.related import (
    ForeignKey, ManyToManyField, OneToOneField, RelatedField,
)
from django.contrib.contenttypes.fields import GenericRelation
from django.template import Context, Template, loader
from django.utils.encoding import force_bytes
from django.utils.safestring import mark_safe
from django.utils.translation import activate as activate_language


__version__ = "1.0"
__license__ = "Python"
__author__ = "Bas van Oostveen <v.oostveen@gmail.com>",
__contributors__ = [
    "Antonio Cavedoni <http://cavedoni.com/>"
    "Stefano J. Attardi <http://attardi.org/>",
    "limodou <http://www.donews.net/limodou/>",
    "Carlo C8E Miron",
    "Andre Campos <cahenan@gmail.com>",
    "Justin Findlay <jfindlay@gmail.com>",
    "Alexander Houben <alexander@houben.ch>",
    "Joern Hees <gitdev@joernhees.de>",
    "Kevin Cherepski <cherepski@gmail.com>",
    "Jose Tomas Tocino <theom3ga@gmail.com>",
    "Adam Dobrawy <naczelnik@jawnosc.tk>",
    "Mikkel Munch Mortensen <https://www.detfalskested.dk/>",
]


def parse_file_or_list(arg):
    if not arg:
        return []
    if isinstance(arg, (list, tuple, set)):
        return arg
    if ',' not in arg and os.path.isfile(arg):
        return [e.strip() for e in open(arg).readlines()]
    return [e.strip() for e in arg.split(',')]


def use_model(model_name, include_models, exclude_models):
    """
    Decide whether to use a model, based on the model name and the lists of
    models to exclude and include.
    """
    # Check against exclude list.
    if exclude_models:
        for model_pattern in exclude_models:
            model_pattern = \
                '^%s$' % model_pattern.replace('*', '.*')
            if re.search(model_pattern, model_name):
                return False
    # Check against exclude list.
    elif include_models:
        for model_pattern in include_models:
            model_pattern = \
                '^%s$' % model_pattern.replace('*', '.*')
            if re.search(model_pattern, model_name):
                return True
    # Return `True` if `include_models` is falsey, otherwise return `False`.
    return not include_models


def generate_graph_data(app_labels, **kwargs):
    cli_options = kwargs.get('cli_options', None)
    disable_fields = kwargs.get('disable_fields', False)
    include_models = parse_file_or_list(kwargs.get('include_models', ""))
    all_applications = kwargs.get('all_applications', False)
    use_subgraph = kwargs.get('group_models', False)
    verbose_names = kwargs.get('verbose_names', False)
    inheritance = kwargs.get('inheritance', True)
    relations_as_fields = kwargs.get("relations_as_fields", True)
    sort_fields = kwargs.get("sort_fields", True)
    language = kwargs.get('language', None)
    if language is not None:
        activate_language(language)
    exclude_columns = parse_file_or_list(kwargs.get('exclude_columns', ""))
    exclude_models = parse_file_or_list(kwargs.get('exclude_models', ""))

    def skip_field(field):
        if exclude_columns:
            if verbose_names and field.verbose_name:
                if field.verbose_name in exclude_columns:
                    return True
            if field.name in exclude_columns:
                return True
        return False

    if all_applications:
        app_labels = [app.label for app in apps.get_app_configs()]

    graphs = []
    for app_label in app_labels:
        app = apps.get_app_config(app_label)
        if not app:
            continue
        graph = Context({
            'name': '"%s"' % app.name,
            'app_name': "%s" % app.name,
            'cluster_app_name': "cluster_%s" % app.name.replace(".", "_"),
            'models': []
        })

        appmodels = list(app.get_models())
        abstract_models = []
        for appmodel in appmodels:
            abstract_models = abstract_models + [abstract_model for abstract_model in appmodel.__bases__ if hasattr(abstract_model, '_meta') and abstract_model._meta.abstract]
        abstract_models = list(set(abstract_models))  # remove duplicates
        appmodels = abstract_models + appmodels

        for appmodel in appmodels:
            appmodel_abstracts = [abstract_model.__name__ for abstract_model in appmodel.__bases__ if hasattr(abstract_model, '_meta') and abstract_model._meta.abstract]

            # collect all attribs of abstract superclasses
            def getBasesAbstractFields(c):
                _abstract_fields = []
                for e in c.__bases__:
                    if hasattr(e, '_meta') and e._meta.abstract:
                        _abstract_fields.extend(e._meta.fields)
                        _abstract_fields.extend(getBasesAbstractFields(e))
                return _abstract_fields
            abstract_fields = getBasesAbstractFields(appmodel)

            model = {
                'app_name': appmodel.__module__.replace(".", "_"),
                'name': appmodel.__name__,
                'abstracts': appmodel_abstracts,
                'fields': [],
                'relations': []
            }

            if not use_model(
                appmodel._meta.object_name,
                include_models,
                exclude_models
            ):
                continue

            if verbose_names and appmodel._meta.verbose_name:
                model['label'] = force_bytes(appmodel._meta.verbose_name)
            else:
                model['label'] = model['name']

            # model attributes
            def add_attributes(field):
                if verbose_names and field.verbose_name:
                    label = force_bytes(field.verbose_name)
                    if label.islower():
                        label = label.capitalize()
                else:
                    label = field.name

                t = type(field).__name__
                if isinstance(field, (OneToOneField, ForeignKey)):
                    t += " ({0})".format(field.rel.field_name)
                # TODO: ManyToManyField, GenericRelation

                model['fields'].append({
                    'name': field.name,
                    'label': label,
                    'type': t,
                    'blank': field.blank,
                    'abstract': field in abstract_fields,
                    'relation': isinstance(field, RelatedField),
                    'primary_key': field.primary_key,
                })

            attributes = [field for field in appmodel._meta.local_fields]
            if not relations_as_fields:
                # Find all the 'real' attributes. Relations are depicted as graph edges instead of attributes
                attributes = [field for field in attributes if not isinstance(field, RelatedField)]

            # find primary key and print it first, ignoring implicit id if other pk exists
            pk = appmodel._meta.pk
            if pk and not appmodel._meta.abstract and pk in attributes:
                add_attributes(pk)

            for field in attributes:
                if skip_field(field):
                    continue
                if pk and field == pk:
                    continue
                add_attributes(field)

            if sort_fields:
                model['fields'] = sorted(model['fields'], key=lambda field: (not field['primary_key'], not field['relation'], field['label']))

            # FIXME: actually many_to_many fields aren't saved in this model's db table, so why should we add an attribute-line for them in the resulting graph?
            # if appmodel._meta.many_to_many:
            #    for field in appmodel._meta.many_to_many:
            #        if skip_field(field):
            #            continue
            #        add_attributes(field)

            # relations
            def add_relation(field, extras=""):
                if verbose_names and field.verbose_name:
                    label = force_bytes(field.verbose_name)
                    if label.islower():
                        label = label.capitalize()
                else:
                    label = field.name

                # show related field name
                if hasattr(field, 'related_query_name'):
                    related_query_name = field.related_query_name()
                    if verbose_names and related_query_name.islower():
                        related_query_name = related_query_name.replace('_', ' ').capitalize()
                    label = '{} ({})'.format(label, force_bytes(related_query_name))

                # handle self-relationships and lazy-relationships
                if isinstance(field.rel.to, six.string_types):
                    if field.rel.to == 'self':
                        target_model = field.model
                    else:
                        if '.' in field.rel.to:
                            app_label, model_name = field.rel.to.split('.', 1)
                        else:
                            app_label = field.model._meta.app_label
                            model_name = field.rel.to
                        target_model = apps.get_model(app_label, model_name)
                else:
                    target_model = field.rel.to

                _rel = {
                    'target_app': target_model.__module__.replace('.', '_'),
                    'target': target_model.__name__,
                    'type': type(field).__name__,
                    'name': field.name,
                    'label': label,
                    'arrows': extras,
                    'needs_node': True
                }
                if _rel not in model['relations'] and use_model(
                    _rel['target'],
                    include_models,
                    exclude_models
                ):
                    model['relations'].append(_rel)

            for field in appmodel._meta.local_fields:
                if field.attname.endswith('_ptr_id'):  # excluding field redundant with inheritance relation
                    continue
                if field in abstract_fields:  # excluding fields inherited from abstract classes. they too show as local_fields
                    continue
                if skip_field(field):
                    continue
                if isinstance(field, OneToOneField):
                    add_relation(field, '[arrowhead=none, arrowtail=none, dir=both]')
                elif isinstance(field, ForeignKey):
                    add_relation(field, '[arrowhead=none, arrowtail=dot, dir=both]')

            for field in appmodel._meta.local_many_to_many:
                if skip_field(field):
                    continue
                if isinstance(field, ManyToManyField):
                    if hasattr(field.rel.through, '_meta') and field.rel.through._meta.auto_created:
                        add_relation(field, '[arrowhead=dot arrowtail=dot, dir=both]')
                elif isinstance(field, GenericRelation):
                    add_relation(field, mark_safe('[style="dotted", arrowhead=normal, arrowtail=normal, dir=both]'))

            if inheritance:
                # add inheritance arrows
                for parent in appmodel.__bases__:
                    if hasattr(parent, "_meta"):  # parent is a model
                        l = "multi-table"
                        if parent._meta.abstract:
                            l = "abstract"
                        if appmodel._meta.proxy:
                            l = "proxy"
                        l += r"\ninheritance"
                        _rel = {
                            'target_app': parent.__module__.replace(".", "_"),
                            'target': parent.__name__,
                            'type': "inheritance",
                            'name': "inheritance",
                            'label': l,
                            'arrows': '[arrowhead=empty, arrowtail=none, dir=both]',
                            'needs_node': True,
                        }
                        # TODO: seems as if abstract models aren't part of models.getModels, which is why they are printed by this without any attributes.
                        if _rel not in model['relations'] and use_model(
                            _rel['target'],
                            include_models,
                            exclude_columns
                        ):
                            model['relations'].append(_rel)

            graph['models'].append(model)
        if graph['models']:
            graphs.append(graph)

    nodes = []
    for graph in graphs:
        nodes.extend([e['name'] for e in graph['models']])

    for graph in graphs:
        for model in graph['models']:
            for relation in model['relations']:
                if relation['target'] in nodes:
                    relation['needs_node'] = False

    now = datetime.datetime.now()
    graph_data = {
        'created_at': now.strftime("%Y-%m-%d %H:%M"),
        'cli_options': cli_options,
        'disable_fields': disable_fields,
        'use_subgraph': use_subgraph,
        'graphs': graphs,
    }
    return graph_data


def generate_dot(graph_data):
    t = loader.get_template('django_extensions/graph_models/digraph.dot')

    if not isinstance(t, Template) and not (hasattr(t, 'template') and isinstance(t.template, Template)):
        raise Exception("Default Django template loader isn't used. "
                        "This can lead to the incorrect template rendering. "
                        "Please, check the settings.")

    c = Context(graph_data).flatten()
    dot = t.render(c)

    return dot
