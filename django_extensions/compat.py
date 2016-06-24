# coding=utf-8
from __future__ import unicode_literals

import importlib
import sys
from optparse import make_option
import django
from django.apps import apps
from django.conf import settings
from django.core.management.base import (BaseCommand, AppCommand, LabelCommand,
                                         CommandError)

# flake8: noqa

#
# Python compatibility
#
PY3 = sys.version_info[0] == 3

if PY3:  # pragma: no cover
    from io import StringIO
else:  # pragma: no cover
    from cStringIO import StringIO

#
# Django compatibility
#
def load_tag_library(libname):
    """Load a templatetag library on multiple Django versions.

    Returns None if the library isn't loaded.
    """
    if django.VERSION < (1, 9):
        from django.template.base import get_library, InvalidTemplateLibrary
        try:
            lib = get_library(libname)
            return lib
        except InvalidTemplateLibrary:
            return None
    else:
        from django.template.backends.django import get_installed_libraries
        from django.template.library import InvalidTemplateLibrary
        try:
            lib = get_installed_libraries()[libname]
            lib = importlib.import_module(lib).register
            return lib
        except (InvalidTemplateLibrary, KeyError):
            return None


def add_to_builtins_compat(name):
    if django.VERSION < (1, 9):
        from django.template.base import add_to_builtins
        add_to_builtins(name)
    else:
        from django.template import engines
        engines['django'].engine.builtins.append(name)


class ProxyParser(object):
    """Faux parser object that will ferry our arguments into options."""

    def __init__(self, command):
        self.command = command

    def add_argument(self, *args, **kwargs):
        """Transform our argument into an option to append to self.option_list.

        In argparse, "available specifiers [in help strings] include the
        program name, %(prog)s and most keyword arguments to add_argument()".
        However, optparse only mentions %default in the help string, and we
        must alter the format to properly replace in optparse without error.
        """
        if 'help' in kwargs:
            kwargs['help'] = kwargs['help'].replace('%(default)s', '%default')
        self.command.option_list += (make_option(*args, **kwargs), )

class CompatibilityBaseCommand(BaseCommand):
    """Provides a compatibility between optparse and argparse transition.

    Starting in Django 1.8, argparse is used. In Django 1.9, optparse support
    will be removed.

    For optparse, you append to the option_list class attribute.
    For argparse, you must define add_arguments(self, parser).
    BaseCommand uses the presence of option_list to decide what course to take.
    """

    def __init__(self, *args, **kwargs):
        if django.VERSION < (1, 8) and hasattr(self, 'add_arguments'):
            self.option_list = BaseCommand.option_list
            parser = ProxyParser(self)
            self.add_arguments(parser)
        super(CompatibilityBaseCommand, self).__init__(*args, **kwargs)


class CompatibilityAppCommand(AppCommand, CompatibilityBaseCommand):
    """AppCommand is a BaseCommand sub-class without its own __init__."""


class CompatibilityLabelCommand(LabelCommand, CompatibilityBaseCommand):
    """LabelCommand is a BaseCommand sub-class without its own __init__."""
