"""
modelviz.py - DOT file generator for Django Models

Based on:
  Django model to DOT (Graphviz) converter
  by Antonio Cavedoni <antonio@cavedoni.org>
  Adapted to be used with django-extensions
"""

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
]

import os
import six
import datetime
from django.utils.translation import activate as activate_language
from django.utils.safestring import mark_safe
from django.template import Context, loader, Template
from django.db import models
from django.db.models import get_models
from django.db.models.fields.related import ForeignKey, OneToOneField, ManyToManyField, RelatedField

try:
    from django.db.models.fields.generic import GenericRelation
    assert GenericRelation
except ImportError:
    from django.contrib.contenttypes.generic import GenericRelation


def parse_file_or_list(arg):
    if not arg:
        return []
    if ',' not in arg and os.path.isfile(arg):
        return [e.strip() for e in open(arg).readlines()]
    return arg.split(',')


def generate_dot(app_labels, **kwargs):
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

    apps = []
    if all_applications:
        apps = models.get_apps()

    for app_label in app_labels:
        app = models.get_app(app_label)
        if app not in apps:
            apps.append(app)

    graphs = []
    for app in apps:
        graph = Context({
            'name': '"%s"' % app.__name__,
            'app_name': "%s" % '.'.join(app.__name__.split('.')[:-1]),
            'cluster_app_name': "cluster_%s" % app.__name__.replace(".", "_"),
            'models': []
        })

        appmodels = get_models(app)
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

            # consider given model name ?
            def consider(model_name):
                if exclude_models and model_name in exclude_models:
                    return False
                elif include_models and model_name not in include_models:
                    return False
                return not include_models or model_name in include_models

            if not consider(appmodel._meta.object_name):
                continue

            if verbose_names and appmodel._meta.verbose_name:
                model['label'] = appmodel._meta.verbose_name.decode("utf8")
            else:
                model['label'] = model['name']

            # model attributes
            def add_attributes(field):
                if verbose_names and field.verbose_name:
                    label = field.verbose_name.decode("utf8")
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
            #if appmodel._meta.many_to_many:
            #    for field in appmodel._meta.many_to_many:
            #        if skip_field(field):
            #            continue
            #        add_attributes(field)

            # relations
            def add_relation(field, extras=""):
                if verbose_names and field.verbose_name:
                    label = field.verbose_name.decode("utf8")
                    if label.islower():
                        label = label.capitalize()
                else:
                    label = field.name

                # show related field name
                if hasattr(field, 'related_query_name'):
                    related_query_name = field.related_query_name()
                    if verbose_names and related_query_name.islower():
                        related_query_name = related_query_name.replace('_', ' ').capitalize()
                    label += ' (%s)' % related_query_name

                # handle self-relationships and lazy-relationships
                if isinstance(field.rel.to, six.string_types):
                    if field.rel.to == 'self':
                        target_model = field.model
                    else:
                        raise Exception("Lazy relationship for model (%s) must be explicit for field (%s)" % (field.model.__name__, field.name))
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
                if _rel not in model['relations'] and consider(_rel['target']):
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
                    if (getattr(field, 'creates_table', False) or  # django 1.1.
                            (hasattr(field.rel.through, '_meta') and field.rel.through._meta.auto_created)):  # django 1.2
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
                        if _rel not in model['relations'] and consider(_rel['target']):
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
    t = loader.get_template('django_extensions/graph_models/digraph.dot')

    if not isinstance(t, Template):
        raise Exception("Default Django template loader isn't used. "
                        "This can lead to the incorrect template rendering. "
                        "Please, check the settings.")

    c = Context({
        'created_at': now.strftime("%Y-%m-%d %H:%M"),
        'cli_options': cli_options,
        'disable_fields': disable_fields,
        'use_subgraph': use_subgraph,
        'graphs': graphs,
    })
    dot = t.render(c)

    return dot
