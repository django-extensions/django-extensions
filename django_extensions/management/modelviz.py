#!/usr/bin/env python

"""Django model to DOT (Graphviz) converter
by Antonio Cavedoni <antonio@cavedoni.org>

Make sure your DJANGO_SETTINGS_MODULE is set to your project or
place this script in the same directory of the project and call
the script like this:

$ python modelviz.py [-h] [-a] [-d] [-g] [-n] [-L <language>] [-i <model_names>] <app_label> ... <app_label> > <filename>.dot
$ dot <filename>.dot -Tpng -o <filename>.png

options:
    -h, --help
    show this help message and exit.

    -a, --all_applications
    show models from all applications.

    -d, --disable_fields
    don't show the class member fields.

    -g, --group_models
    draw an enclosing box around models from the same app.

    -i, --include_models=User,Person,Car
    only include selected models in graph.

    -n, --verbose_names
    use verbose_name for field and models.

    -L, --language
    specify language used for verrbose_name localization

    -x, --exclude_columns
    exclude specific column(s) from the graph.

    -X, --exclude_models
    exclude specific model(s) from the graph.
    
    -e, --inheritance
    show inheritance arrows.
"""
__version__ = "0.9"
__svnid__ = "$Id$"
__license__ = "Python"
__author__ = "Antonio Cavedoni <http://cavedoni.com/>"
__contributors__ = [
   "Stefano J. Attardi <http://attardi.org/>",
   "limodou <http://www.donews.net/limodou/>",
   "Carlo C8E Miron",
   "Andre Campos <cahenan@gmail.com>",
   "Justin Findlay <jfindlay@gmail.com>",
   "Alexander Houben <alexander@houben.ch>",
   "Bas van Oostveen <v.oostveen@gmail.com>",
   "Joern Hees <gitdev@joernhees.de>"
]

import os
import sys
import getopt

from django.core.management import setup_environ

try:
    import settings
except ImportError:
    pass
else:
    setup_environ(settings)

from django.utils.translation import activate as activate_language
from django.utils.safestring import mark_safe
from django.template import Template, Context, loader
from django.db import models
from django.db.models import get_models
from django.db.models.fields.related import \
    ForeignKey, OneToOneField, ManyToManyField, RelatedField

try:
    from django.db.models.fields.generic import GenericRelation
except ImportError:
    from django.contrib.contenttypes.generic import GenericRelation

def parse_file_or_list(arg):
    if not arg:
        return []
    if not ',' in arg and os.path.isfile(arg):
        return [e.strip() for e in open(arg).readlines()]
    return arg.split(',')


def generate_dot(app_labels, **kwargs):
    disable_fields = kwargs.get('disable_fields', False)
    include_models = parse_file_or_list(kwargs.get('include_models', ""))
    all_applications = kwargs.get('all_applications', False)
    use_subgraph = kwargs.get('group_models', False)
    verbose_names = kwargs.get('verbose_names', False)
    inheritance = kwargs.get('inheritance', False)
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




    t = loader.get_template('django_extensions/graph_models/head.html')
    c = Context({})
    dot = t.render(c)

    apps = []
    if all_applications:
        apps = models.get_apps()

    for app_label in app_labels:
        app = models.get_app(app_label)
        if not app in apps:
            apps.append(app)

    graphs = []
    for app in apps:
        graph = Context({
            'name': '"%s"' % app.__name__,
            'app_name': "%s" % '.'.join(app.__name__.split('.')[:-1]),
            'cluster_app_name': "cluster_%s" % app.__name__.replace(".", "_"),
            'disable_fields': disable_fields,
            'use_subgraph': use_subgraph,
            'models': []
        })

        appmodels = get_models(app)
        abstract_models = []
        for appmodel in appmodels:
            abstract_models = abstract_models + [abstract_model for abstract_model in appmodel.__bases__ if hasattr(abstract_model, '_meta') and abstract_model._meta.abstract]
        abstract_models = list(set(abstract_models)) # remove duplicates
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
                return not include_models or model_name in include_models

            if not consider(appmodel._meta.object_name):
                continue

            if verbose_names and appmodel._meta.verbose_name:
                model['label'] = appmodel._meta.verbose_name
            else:
                model['label'] = model['name']

            # model attributes
            def add_attributes(field):
                if verbose_names and field.verbose_name:
                    label = field.verbose_name
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
                })

            # Find all the real attributes. Relations are depicted as graph edges instead of attributes
            attributes = [field for field in appmodel._meta.local_fields if not isinstance(field, RelatedField)]

            # find primary key and print it first, ignoring implicit id if other pk exists
            pk = appmodel._meta.pk
            if not appmodel._meta.abstract and pk in attributes:
                add_attributes(pk)
            for field in attributes:
                if skip_field(field):
                    continue
                if not field.primary_key:
                    add_attributes(field)
            
            # FIXME: actually many_to_many fields aren't saved in this model's db table, so why should we add an attribute-line for them in the resulting graph?
            #if appmodel._meta.many_to_many:
            #    for field in appmodel._meta.many_to_many:
            #        if skip_field(field):
            #            continue
            #        add_attributes(field)

            # relations
            def add_relation(field, extras=""):
                if verbose_names and field.verbose_name:
                    label = field.verbose_name
                else:
                    label = field.name
                    
                # show related field name
                if hasattr(field, 'related_query_name'):
                    label += ' (%s)' % field.related_query_name()

                _rel = {
                    'target_app': field.rel.to.__module__.replace('.', '_'),
                    'target': field.rel.to.__name__,
                    'type': type(field).__name__,
                    'name': field.name,
                    'label': label,
                    'arrows': extras,
                    'needs_node': True
                }
                if _rel not in model['relations'] and consider(_rel['target']):
                    model['relations'].append(_rel)

            for field in appmodel._meta.local_fields:
                if field.attname.endswith('_ptr_id'): # excluding field redundant with inheritance relation
                    continue
                if field in abstract_fields: # excluding fields inherited from abstract classes. they too show as local_fields
                    continue
                if skip_field(field):
                    continue
                if isinstance(field, OneToOneField):
                    add_relation(field, '[arrowhead=none, arrowtail=none]')
                elif isinstance(field, ForeignKey):
                    add_relation(field, '[arrowhead=none, arrowtail=dot]')

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
                    if hasattr(parent, "_meta"): # parent is a model
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
                            'arrows': '[arrowhead=empty, arrowtail=none]',
                            'needs_node': True
                        }
                        # TODO: seems as if abstract models aren't part of models.getModels, which is why they are printed by this without any attributes.
                        if _rel not in model['relations'] and consider(_rel['target']):
                            model['relations'].append(_rel)
            
            graph['models'].append(model)
        graphs.append(graph)

    nodes = []
    for graph in graphs:
        nodes.extend([e['name'] for e in graph['models']])

    for graph in graphs:
        # don't draw duplication nodes because of relations
        for model in graph['models']:
            for relation in model['relations']:
                if relation['target'] in nodes:
                    relation['needs_node'] = False
        # render templates
        t = loader.get_template('django_extensions/graph_models/body.html')
        dot += '\n' + t.render(graph)

    for graph in graphs:
        t = loader.get_template('django_extensions/graph_models/rel.html')
        dot += '\n' + t.render(graph)


    t = loader.get_template('django_extensions/graph_models/tail.html')
    c = Context({})
    dot += '\n' + t.render(c)
    return dot

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hadgi:L:x:X:en",
                    ["help", "all_applications", "disable_fields", "group_models", "include_models=", "inheritance", "verbose_names", "language=", "exclude_columns=", "exclude_models="])
    except getopt.GetoptError, error:
        print __doc__
        sys.exit(error)

    kwargs = {}
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print __doc__
            sys.exit()
        if opt in ("-a", "--all_applications"):
            kwargs['all_applications'] = True
        if opt in ("-d", "--disable_fields"):
            kwargs['disable_fields'] = True
        if opt in ("-g", "--group_models"):
            kwargs['group_models'] = True
        if opt in ("-i", "--include_models"):
            kwargs['include_models'] = arg
        if opt in ("-e", "--inheritance"):
            kwargs['inheritance'] = True
        if opt in ("-n", "--verbose-names"):
            kwargs['verbose_names'] = True
        if opt in ("-L", "--language"):
            kwargs['language'] = arg
        if opt in ("-x", "--exclude_columns"):
            kwargs['exclude_columns'] = arg
        if opt in ("-X", "--exclude_models"):
            kwargs['exclude_models'] = arg

    if not args and not kwargs.get('all_applications', False):
        print __doc__
        sys.exit()

    print generate_dot(args, **kwargs)

if __name__ == "__main__":
    main()
