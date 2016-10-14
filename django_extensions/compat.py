# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import importlib
import django

from django.conf import settings


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


def get_template_setting(template_key, default=None):
    """ Read template settings pre and post django 1.8 """
    templates_var = getattr(settings, 'TEMPLATES', None)
    if templates_var is not None and template_key in templates_var[0]:
        return templates_var[0][template_key]
    if template_key == 'DIRS':
        pre18_template_key = 'TEMPLATES_%s' % template_key
        value = getattr(settings, pre18_template_key, default)
        return value
    return default
