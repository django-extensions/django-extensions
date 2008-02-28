#!/usr/bin/env python
"""Django model to DOT (Graphviz) converter
by Antonio Cavedoni <antonio@cavedoni.org>

Make sure your DJANGO_SETTINGS_MODULE is set to your project or
place this script in the same directory of the project and call
the script like this:

$ python modelviz.py [-h] [-d] <app_label> ... <app_label> > <filename>.dot
$ dot <filename>.dot -Tpng -o <filename>.png

options:
    -h, --help
    show this help message and exit.

    -d, --disable_fields
    don't show the class member fields.
"""
__version__ = "0.8"
__svnid__ = "$Id$"
__license__ = "Python"
__author__ = "Antonio Cavedoni <http://cavedoni.com/>"
__contributors__ = [
   "Stefano J. Attardi <http://attardi.org/>",
   "limodou <http://www.donews.net/limodou/>",
   "Carlo C8E Miron",
   "Andre Campos <cahenan@gmail.com>",
   "Justin Findlay <jfindlay@gmail.com>",
   ]

import getopt, sys

from django.core.management import setup_environ

try:
    import settings
except ImportError:
    pass
else:
    setup_environ(settings)

from django.template import Template, Context
from django.db import models
from django.db.models import get_models
from django.db.models.fields.related import \
    ForeignKey, OneToOneField, ManyToManyField

try:
    from django.db.models.fields.generic import GenericRelation
except ImportError:
    from django.contrib.contenttypes.generic import GenericRelation

head_template = """
digraph name {
  fontname = "Helvetica"
  fontsize = 8

  node [
    fontname = "Helvetica"
    fontsize = 8
    shape = "plaintext"
  ]
   edge [
    fontname = "Helvetica"
    fontsize = 8
  ]

"""

body_template = """
  {% for model in models %}
    {% for relation in model.relations %}
    {{ relation.target }} [label=<
        <TABLE BGCOLOR="palegoldenrod" BORDER="0" CELLBORDER="0" CELLSPACING="0">
        <TR><TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER" BGCOLOR="olivedrab4"
        ><FONT FACE="Helvetica Bold" COLOR="white"
        >{{ relation.target }}</FONT></TD></TR>
        </TABLE>
        >]
    {{ model.name }} -> {{ relation.target }}
    [label="{{ relation.name }}"] {{ relation.arrows }};
    {% endfor %}
  {% endfor %}

  {% for model in models %}
    {{ model.name }} [label=<
    <TABLE BGCOLOR="palegoldenrod" BORDER="0" CELLBORDER="0" CELLSPACING="0">
     <TR><TD COLSPAN="2" CELLPADDING="4" ALIGN="CENTER" BGCOLOR="olivedrab4"
     ><FONT FACE="Helvetica Bold" COLOR="white"
     >{{ model.name }}</FONT></TD></TR>

    {% if not disable_fields %}
        {% for field in model.fields %}
        <TR><TD ALIGN="LEFT" BORDER="0"
        ><FONT {% if field.blank %}COLOR="#7B7B7B" {% endif %}FACE="Helvetica Bold">{{ field.name }}</FONT
        ></TD>
        <TD ALIGN="LEFT"
        ><FONT {% if field.blank %}COLOR="#7B7B7B" {% endif %}FACE="Helvetica Bold">{{ field.type }}</FONT
        ></TD></TR>
        {% endfor %}
    {% endif %}
    </TABLE>
    >]
  {% endfor %}
"""

tail_template = """
}
"""

def generate_dot(app_labels, **kwargs):
    disable_fields = kwargs.get('disable_fields', False)
    all_applications = kwargs.get('all_applications', False)
    
    dot = head_template

    apps = []
    if all_applications:
        apps = models.get_apps()
    
    for app_label in app_labels:
        app = models.get_app(app_label)
        if not app in apps:
            apps.append(app)

    for app in apps:
        graph = Context({
            'name': '"%s"' % app.__name__,
            'disable_fields': disable_fields,
            'models': []
            })

        for appmodel in get_models(app):
            model = {
                'name': appmodel.__name__,
                'fields': [],
                'relations': []
                }

            # model attributes
            def add_attributes():
                model['fields'].append({
                    'name': field.name,
                    'type': type(field).__name__,
                    'blank': field.blank
                    })

            for field in appmodel._meta.fields:
                add_attributes()

            if appmodel._meta.many_to_many:
                for field in appmodel._meta.many_to_many:
                    add_attributes()

            # relations
            def add_relation(extras=""):
                _rel = {
                    'target': field.rel.to.__name__,
                    'type': type(field).__name__,
                    'name': field.name,
                    'arrows': extras
                    }
                if _rel not in model['relations']:
                    model['relations'].append(_rel)

            for field in appmodel._meta.fields:
                if isinstance(field, ForeignKey):
                    add_relation()
                elif isinstance(field, OneToOneField):
                    add_relation("[arrowhead=none arrowtail=none]")

            if appmodel._meta.many_to_many:
                for field in appmodel._meta.many_to_many:
                    if isinstance(field, ManyToManyField):
                        add_relation("[arrowhead=normal arrowtail=normal]")
                    elif isinstance(field, GenericRelation):
                        add_relation(
                            '[style="dotted"] [arrowhead=normal arrowtail=normal]')
            graph['models'].append(model)

        t = Template(body_template)
        dot += '\n' + t.render(graph)

    dot += '\n' + tail_template

    return dot

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd",
                    ["help", "disable_fields"])
    except getopt.GetoptError, error:
        print __doc__
        sys.exit(error)
    else:
        if not args:
            print __doc__
            sys.exit()

    kwargs = {}
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print __doc__
            sys.exit()
        if opt in ("-d", "--disable_fields"):
            kwargs['disable_fields'] = True
    print generate_dot(args, **kwargs)

if __name__ == "__main__":
    main()
