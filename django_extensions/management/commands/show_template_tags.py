# coding=utf-8
import inspect
import os

import six
from django.conf import settings
from django.core.management import color
from django.utils import termcolors

from django_extensions.compat import load_tag_library
from django_extensions.management.utils import signalcommand
from django_extensions.compat import CompatibilityBaseCommand as BaseCommand

try:
    from django.utils.encoding import smart_text
except ImportError:
    smart_text = six.u


def color_style():
    style = color.color_style()
    style.FILTER = termcolors.make_style(fg='yellow', opts=('bold',))
    style.MODULE_NAME = termcolors.make_style(fg='green', opts=('bold',))
    style.TAG = termcolors.make_style(fg='red', opts=('bold',))
    style.TAGLIB = termcolors.make_style(fg='blue', opts=('bold',))
    return style


def format_block(block, nlspaces=0):
    """Format the given block of text, trimming leading/trailing
    empty lines and any leading whitespace that is common to all lines.
    The purpose is to let us list a code block as a multiline,
    triple-quoted Python string, taking care of
    indentation concerns.
    http://code.activestate.com/recipes/145672/"""

    import re

    # separate block into lines
    lines = smart_text(block).split('\n')

    # remove leading/trailing empty lines
    while lines and not lines[0]:
        del lines[0]
    while lines and not lines[-1]:
        del lines[-1]

    # look at first line to see how much indentation to trim
    ws = re.match(r'\s*', lines[0]).group(0)
    if ws:
        lines = map(lambda x: x.replace(ws, '', 1), lines)

    # remove leading/trailing blank lines (after leading ws removal)
    # we do this again in case there were pure-whitespace lines
    while lines and not lines[0]:
        del lines[0]
    while lines and not lines[-1]:
        del lines[-1]

    # account for user-specified leading spaces
    flines = ['%s%s' % (' ' * nlspaces, line) for line in lines]

    return '\n'.join(flines) + '\n'


class Command(BaseCommand):
    help = "Displays template tags and filters available in the current project."
    results = ""

    def add_result(self, s, depth=0):
        self.results += '%s\n' % s.rjust(depth * 4 + len(s))

    @signalcommand
    def handle(self, *args, **options):
        if args:
            appname, = args

        style = color_style()

        if getattr(settings, 'ADMIN_FOR', None):
            settings_modules = [__import__(m, {}, {}, ['']) for m in settings.ADMIN_FOR]
        else:
            settings_modules = [settings]

        for settings_mod in settings_modules:
            for app in settings_mod.INSTALLED_APPS:
                try:
                    templatetag_mod = __import__(app + '.templatetags', {}, {}, [''])
                except ImportError:
                    continue
                mod_path = inspect.getabsfile(templatetag_mod)
                mod_files = os.listdir(os.path.dirname(mod_path))
                tag_files = [i.rstrip('.py') for i in mod_files if i.endswith('.py') and i[0] != '_']
                app_labeled = False
                for taglib in tag_files:
                    lib = load_tag_library(taglib)
                    if lib is None:
                        continue

                    if not app_labeled:
                        self.add_result('App: %s' % style.MODULE_NAME(app))
                        app_labeled = True
                    self.add_result('load: %s' % style.TAGLIB(taglib), 1)
                    libstuff = [
                        (lib.tags, 'Tag:', style.TAG),
                        (lib.filters, 'Filter:', style.FILTER)
                    ]
                    for items, label, style_func in libstuff:
                        for item in items:
                            self.add_result('%s %s' % (label, style_func(item)), 2)
                            doc = inspect.getdoc(items[item])
                            if doc:
                                self.add_result(format_block(doc, 12))
        return self.results
