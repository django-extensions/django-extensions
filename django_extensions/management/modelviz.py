# -*- coding: utf-8 -*-
"""
modelviz.py - DOT file generator for Django Models

Based on:
  Django model to DOT (Graphviz) converter
  by Antonio Cavedoni <antonio@cavedoni.org>
  Adapted to be used with django-extensions
"""

# from __future__ import unicode_literals

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
from django.utils.encoding import force_text
from django.utils.safestring import mark_safe
from django.utils.translation import activate as activate_language


__version__ = "1.1"
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
    "Andrzej Bistram <andrzej.bistram@gmail.com>",
    "Daniel Lipsitt <danlipsitt@gmail.com>",
]


def parse_file_or_list(arg):
    if not arg:
        return []
    if isinstance(arg, (list, tuple, set)):
        return arg
    if ',' not in arg and os.path.isfile(arg):
        return [e.strip() for e in open(arg).readlines()]
    return [e.strip() for e in arg.split(',')]


class ModelGraph(object):
    def __init__(self, app_labels, **kwargs):
        self.graphs = []
        self.cli_options = kwargs.get('cli_options', None)
        self.disable_fields = kwargs.get('disable_fields', False)
        self.include_models = parse_file_or_list(
            kwargs.get('include_models', "")
        )
        self.all_applications = kwargs.get('all_applications', False)
        self.use_subgraph = kwargs.get('group_models', False)
        self.verbose_names = kwargs.get('verbose_names', False)
        self.inheritance = kwargs.get('inheritance', True)
        self.relations_as_fields = kwargs.get("relations_as_fields", True)
        self.sort_fields = kwargs.get("sort_fields", True)
        self.language = kwargs.get('language', None)
        if self.language is not None:
            activate_language(self.language)
        self.exclude_columns = parse_file_or_list(
            kwargs.get('exclude_columns', "")
        )
        self.exclude_models = parse_file_or_list(
            kwargs.get('exclude_models', "")
        )
        if self.all_applications:
            self.app_labels = [app.label for app in apps.get_app_configs()]
        else:
            self.app_labels = app_labels

    def generate_graph_data(self):
        self.process_apps()

        nodes = []
        for graph in self.graphs:
            nodes.extend([e['name'] for e in graph['models']])

        for graph in self.graphs:
            for model in graph['models']:
                for relation in model['relations']:
                    if relation is not None:
                        if relation['target'] in nodes:
                            relation['needs_node'] = False

    def get_graph_data(self, as_json=False):
        now = datetime.datetime.now()
        graph_data = {
            'created_at': now.strftime("%Y-%m-%d %H:%M"),
            'cli_options': self.cli_options,
            'disable_fields': self.disable_fields,
            'use_subgraph': self.use_subgraph,
        }

        if as_json:
            graph_data['graphs'] = [context.flatten() for context in self.graphs]
        else:
            graph_data['graphs'] = self.graphs

        return graph_data

    def add_attributes(self, field, abstract_fields):
        if self.verbose_names and field.verbose_name:
            label = force_text(field.verbose_name)
            if label.islower():
                label = label.capitalize()
        else:
            label = field.name

        t = type(field).__name__
        if isinstance(field, (OneToOneField, ForeignKey)):
            t += " ({0})".format(field.remote_field.field_name)
        # TODO: ManyToManyField, GenericRelation

        return {
            'name': field.name,
            'label': label,
            'type': t,
            'blank': field.blank,
            'abstract': field in abstract_fields,
            'relation': isinstance(field, RelatedField),
            'primary_key': field.primary_key,
        }

    def add_relation(self, field, model, extras=""):
        if self.verbose_names and field.verbose_name:
            label = force_text(field.verbose_name)
            if label.islower():
                label = label.capitalize()
        else:
            label = field.name

        # show related field name
        if hasattr(field, 'related_query_name'):
            related_query_name = field.related_query_name()
            if self.verbose_names and related_query_name.islower():
                related_query_name = related_query_name.replace('_', ' ').capitalize()
            label = '{} ({})'.format(label, force_text(related_query_name))

        # handle self-relationships and lazy-relationships
        if isinstance(field.remote_field.model, six.string_types):
            if field.remote_field.model == 'self':
                target_model = field.model
            else:
                if '.' in field.remote_field.model:
                    app_label, model_name = field.remote_field.model.split('.', 1)
                else:
                    app_label = field.model._meta.app_label
                    model_name = field.remote_field.model
                target_model = apps.get_model(app_label, model_name)
        else:
            target_model = field.remote_field.model

        _rel = self.get_relation_context(target_model, field, label, extras)

        if _rel not in model['relations'] and self.use_model(_rel['target']):
            return _rel

    def get_abstract_models(self, appmodels):
        abstract_models = []
        for appmodel in appmodels:
            abstract_models += [abstract_model for abstract_model in
                                appmodel.__bases__ if
                                hasattr(abstract_model, '_meta') and
                                abstract_model._meta.abstract]
        abstract_models = list(set(abstract_models))  # remove duplicates
        return abstract_models

    def get_app_context(self, app):
        return Context({
            'name': '"%s"' % app.name,
            'app_name': "%s" % app.name,
            'cluster_app_name': "cluster_%s" % app.name.replace(".", "_"),
            'models': []
        })

    def get_appmodel_attributes(self, appmodel):
        if self.relations_as_fields:
            attributes = [field for field in appmodel._meta.local_fields]
        else:
            # Find all the 'real' attributes. Relations are depicted as graph edges instead of attributes
            attributes = [field for field in appmodel._meta.local_fields if not
                          isinstance(field, RelatedField)]
        return attributes

    def get_appmodel_abstracts(self, appmodel):
        return [abstract_model.__name__ for abstract_model in
                appmodel.__bases__ if
                hasattr(abstract_model, '_meta') and
                abstract_model._meta.abstract]

    def get_appmodel_context(self, appmodel, appmodel_abstracts):
        context = {
            'app_name': appmodel.__module__.replace(".", "_"),
            'name': appmodel.__name__,
            'abstracts': appmodel_abstracts,
            'fields': [],
            'relations': []
        }

        if self.verbose_names and appmodel._meta.verbose_name:
            context['label'] = force_text(appmodel._meta.verbose_name)
        else:
            context['label'] = context['name']

        return context

    def get_bases_abstract_fields(self, c):
        _abstract_fields = []
        for e in c.__bases__:
            if hasattr(e, '_meta') and e._meta.abstract:
                _abstract_fields.extend(e._meta.fields)
                _abstract_fields.extend(self.get_bases_abstract_fields(e))
        return _abstract_fields

    def get_inheritance_context(self, appmodel, parent):
        label = "multi-table"
        if parent._meta.abstract:
            label = "abstract"
        if appmodel._meta.proxy:
            label = "proxy"
        label += r"\ninheritance"
        return {
            'target_app': parent.__module__.replace(".", "_"),
            'target': parent.__name__,
            'type': "inheritance",
            'name': "inheritance",
            'label': label,
            'arrows': '[arrowhead=empty, arrowtail=none, dir=both]',
            'needs_node': True,
        }

    def get_models(self, app):
        appmodels = list(app.get_models())
        return appmodels

    def get_relation_context(self, target_model, field, label, extras):
        return {
            'target_app': target_model.__module__.replace('.', '_'),
            'target': target_model.__name__,
            'type': type(field).__name__,
            'name': field.name,
            'label': label,
            'arrows': extras,
            'needs_node': True
        }

    def process_attributes(self, field, model, pk, abstract_fields):
        newmodel = model.copy()
        if self.skip_field(field) or pk and field == pk:
            return newmodel
        newmodel['fields'].append(self.add_attributes(field, abstract_fields))
        return newmodel

    def process_apps(self):
        for app_label in self.app_labels:
            app = apps.get_app_config(app_label)
            if not app:
                continue
            app_graph = self.get_app_context(app)
            app_models = self.get_models(app)
            abstract_models = self.get_abstract_models(app_models)
            app_models = abstract_models + app_models

            for appmodel in app_models:
                if not self.use_model(appmodel._meta.object_name):
                    continue
                appmodel_abstracts = self.get_appmodel_abstracts(appmodel)
                abstract_fields = self.get_bases_abstract_fields(appmodel)
                model = self.get_appmodel_context(appmodel, appmodel_abstracts)
                attributes = self.get_appmodel_attributes(appmodel)

                # find primary key and print it first, ignoring implicit id if other pk exists
                pk = appmodel._meta.pk
                if pk and not appmodel._meta.abstract and pk in attributes:
                    model['fields'].append(self.add_attributes(pk, abstract_fields))

                for field in attributes:
                    model = self.process_attributes(field, model, pk, abstract_fields)

                if self.sort_fields:
                    model = self.sort_model_fields(model)

                for field in appmodel._meta.local_fields:
                    model = self.process_local_fields(field, model, abstract_fields)

                for field in appmodel._meta.local_many_to_many:
                    model = self.process_local_many_to_many(field, model)

                if self.inheritance:
                    # add inheritance arrows
                    for parent in appmodel.__bases__:
                        model = self.process_parent(parent, appmodel, model)

                app_graph['models'].append(model)
            if app_graph['models']:
                self.graphs.append(app_graph)

    def process_local_fields(self, field, model, abstract_fields):
        newmodel = model.copy()
        if (field.attname.endswith('_ptr_id') or  # excluding field redundant with inheritance relation
                field in abstract_fields or  # excluding fields inherited from abstract classes. they too show as local_fields
                self.skip_field(field)):
            return newmodel
        if isinstance(field, OneToOneField):
            newmodel['relations'].append(self.add_relation(field, newmodel, '[arrowhead=none, arrowtail=none, dir=both]'))
        elif isinstance(field, ForeignKey):
            newmodel['relations'].append(self.add_relation(field, newmodel, '[arrowhead=none, arrowtail=dot, dir=both]'))
        return newmodel

    def process_local_many_to_many(self, field, model):
        newmodel = model.copy()
        if self.skip_field(field):
            return newmodel
        if isinstance(field, ManyToManyField):
            if hasattr(field.remote_field.through, '_meta') and field.remote_field.through._meta.auto_created:
                newmodel['relations'].append(self.add_relation(field, newmodel, '[arrowhead=dot arrowtail=dot, dir=both]'))
        elif isinstance(field, GenericRelation):
            newmodel['relations'].append(self.add_relation(field, newmodel, mark_safe('[style="dotted", arrowhead=normal, arrowtail=normal, dir=both]')))
        return newmodel

    def process_parent(self, parent, appmodel, model):
        newmodel = model.copy()
        if hasattr(parent, "_meta"):  # parent is a model
            _rel = self.get_inheritance_context(appmodel, parent)
            # TODO: seems as if abstract models aren't part of models.getModels, which is why they are printed by this without any attributes.
            if _rel not in newmodel['relations'] and self.use_model(_rel['target']):
                newmodel['relations'].append(_rel)
        return newmodel

    def sort_model_fields(self, model):
        newmodel = model.copy()
        newmodel['fields'] = sorted(newmodel['fields'], key=lambda field: (not field['primary_key'], not field['relation'], field['label']))
        return newmodel

    def use_model(self, model_name):
        """
        Decide whether to use a model, based on the model name and the lists of
        models to exclude and include.
        """
        # Check against exclude list.
        if self.exclude_models:
            for model_pattern in self.exclude_models:
                model_pattern = '^%s$' % model_pattern.replace('*', '.*')
                if re.search(model_pattern, model_name):
                    return False
        # Check against exclude list.
        elif self.include_models:
            for model_pattern in self.include_models:
                model_pattern = '^%s$' % model_pattern.replace('*', '.*')
                if re.search(model_pattern, model_name):
                    return True
        # Return `True` if `include_models` is falsey, otherwise return `False`.
        return not self.include_models

    def skip_field(self, field):
        if self.exclude_columns:
            if self.verbose_names and field.verbose_name:
                if field.verbose_name in self.exclude_columns:
                    return True
            if field.name in self.exclude_columns:
                return True
        return False


def generate_dot(graph_data, template='django_extensions/graph_models/digraph.dot'):
    t = loader.get_template(template)

    if not isinstance(t, Template) and not (hasattr(t, 'template') and isinstance(t.template, Template)):
        raise Exception("Default Django template loader isn't used. "
                        "This can lead to the incorrect template rendering. "
                        "Please, check the settings.")

    c = Context(graph_data).flatten()
    dot = t.render(c)

    return dot


def generate_graph_data(*args, **kwargs):
    generator = ModelGraph(*args, **kwargs)
    generator.generate_graph_data()
    return generator.get_graph_data()


def use_model(model, include_models, exclude_models):
    generator = ModelGraph([], include_models=include_models, exclude_models=exclude_models)
    return generator.use_model(model)
