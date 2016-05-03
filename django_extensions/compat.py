# coding=utf-8
from __future__ import unicode_literals

import sys
from optparse import make_option
import django
from django.conf import settings
from django.core.management.base import (BaseCommand, AppCommand, LabelCommand,
                                         CommandError)

# flake8: noqa

#
# Python compatibility
#
PY3 = sys.version_info[0] == 3
OLD_PY2 = sys.version_info[:2] < (2, 7)

if PY3:  # pragma: no cover
    from io import StringIO
    import importlib
elif OLD_PY2:  # pragma: no cover
    from cStringIO import StringIO
    from django.utils import importlib
else:  # pragma: no cover
    from cStringIO import StringIO
    import importlib

#
# Django compatibility
#
try:  # Django 1.5
    from django.contrib.auth import get_user_model
except ImportError:  # pragma: no cover
    assert django.VERSION < (1, 5)
    from django.contrib.auth.models import User
    User.USERNAME_FIELD = "username"
    User.get_username = lambda self: self.username

    def get_user_model():
        return User


def list_apps():
    try:
        # django >= 1.7, to support AppConfig
        from django.apps import apps
    except ImportError:
        # old way
        return list(settings.INSTALLED_APPS)
    else:
        return [app.name for app in apps.get_app_configs()]


def list_app_labels():
    try:
        # django >= 1.7, to support AppConfig
        from django.apps import apps
    except ImportError:
        # old way
        return [app.rsplit(".")[-1] for app in settings.INSTALLED_APPS]
    else:
        return [app.label for app in apps.get_app_configs()]


def get_app(app_label):
    try:
        # django >= 1.7
        from django.apps import apps
    except ImportError:
        from django.db import models
        return models.get_app(app_label)
    else:
        return apps.get_app_config(app_label).models_module


def get_apps():
    try:
        # django >= 1.7, to support AppConfig
        from django.apps import apps
    except ImportError:
        from django.db import models
        return models.get_apps()
    else:
        return [app.models_module for app in apps.get_app_configs() if app.models_module]


def get_apps_from_cache():
    try:
        from django.apps import apps
    except ImportError:
        from django.db.models.loading import cache
        return cache.get_apps()
    else:
        return [app.models_module for app in apps.get_app_configs() if app.models_module]


def get_models_from_cache(app):
    try:
        from django.apps import apps
    except ImportError:
        from django.db.models.loading import cache
        return cache.get_models(app)
    else:
        return apps.get_models(app)


def get_app_models(app_labels=None):
    if app_labels is None:
        try:
            # django >= 1.7, to support AppConfig
            from django.apps import apps
        except ImportError:
            from django.db import models
            return models.get_models(include_auto_created=True)
        else:
            return apps.get_models(include_auto_created=True)

    if not isinstance(app_labels, (list, tuple, set)):
        app_labels = [app_labels]

    app_models = []
    try:
        # django >= 1.7, to support AppConfig
        from django.apps import apps
    except ImportError:
        from django.db import models

        try:
            app_list = [models.get_app(app_label) for app_label in app_labels]
        except (models.ImproperlyConfigured, ImportError) as e:
            raise CommandError("%s. Are you sure your INSTALLED_APPS setting is correct?" % e)

        for app in app_list:
            app_models.extend(models.get_models(app, include_auto_created=True))
    else:
        for app_label in app_labels:
            app_config = apps.get_app_config(app_label)
            app_models.extend(app_config.get_models(include_auto_created=True))

    return app_models


def get_model_compat(app_label, model_name):
    """Get a model on multiple Django versions."""
    try:
        # django >= 1.7
        from django.apps import apps
    except ImportError:
        from django.db.models import get_model
        return get_model(app_label, model_name)
    else:
        return apps.get_model(app_label, model_name)


def get_models_for_app(app_label):
    """Returns the models in the given app for an app label."""
    try:
        # django >= 1.7
        from django.apps import apps
    except ImportError:
        from django.db.models import get_app, get_models
        return get_models(get_app(app_label))
    else:
        return apps.get_app_config(app_label).get_models()


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
