# coding=utf-8
from __future__ import unicode_literals

import importlib
import django


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
