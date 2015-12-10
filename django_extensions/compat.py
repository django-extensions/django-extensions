from __future__ import unicode_literals

import sys
import django
from django.conf import settings
from django.core.management.base import CommandError

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
        return [app.name for app in apps.get_app_configs()]
    except ImportError:
        # old way
        return list(settings.INSTALLED_APPS)


def list_app_labels():
    try:
        # django >= 1.7, to support AppConfig
        from django.apps import apps
        return [app.label for app in apps.get_app_configs()]
    except ImportError:
        # old way
        return [app.rsplit(".")[-1] for app in settings.INSTALLED_APPS]


def get_app(app_label):
    try:
        # django >= 1.7
        from django.apps import apps
        return apps.get_app_config(app_label).models_module
    except ImportError:
        from django.db import models
        return models.get_app(app_label)


def get_apps():
    try:
        # django >= 1.7, to support AppConfig
        from django.apps import apps
        return [app.models_module for app in apps.get_app_configs() if app.models_module]
    except ImportError:
        from django.db import models
        return models.get_apps()


def get_apps_from_cache():
    try:
        from django.apps import apps
        return [app.models_module for app in apps.get_app_configs() if app.models_module]
    except ImportError:
        from django.db.models.loading import cache
        return cache.get_apps()


def get_models_from_cache(app):
    try:
        from django.apps import apps
        return apps.get_models(app)
    except ImportError:
        from django.db.models.loading import cache
        return cache.get_models(app)


def get_app_models(app_labels=None):
    if app_labels is None:
        try:
            # django >= 1.7, to support AppConfig
            from django.apps import apps
            return apps.get_models(include_auto_created=True)
        except ImportError:
            from django.db import models
            return models.get_models(include_auto_created=True)

    if not isinstance(app_labels, (list, tuple, set)):
        app_labels = [app_labels]

    app_models = []
    try:
        # django >= 1.7, to support AppConfig
        from django.apps import apps

        for app_label in app_labels:
            app_config = apps.get_app_config(app_label)
            app_models.extend(app_config.get_models(include_auto_created=True))
    except ImportError:
        from django.db import models

        try:
            app_list = [models.get_app(app_label) for app_label in app_labels]
        except (models.ImproperlyConfigured, ImportError) as e:
            raise CommandError("%s. Are you sure your INSTALLED_APPS setting is correct?" % e)

        for app in app_list:
            app_models.extend(models.get_models(app, include_auto_created=True))

    return app_models


def get_model_compat(app_label, model_name):
    """Get a model on multiple Django versions."""
    try:
        # django >= 1.7
        from django.apps import apps
        return apps.get_model(app_label, model_name)
    except ImportError:
        from django.db.models import get_model
        return get_model(app_label, model_name)


def get_models_compat(app_label):
    """Get models on multiple Django versions."""
    try:
        # django >= 1.7
        from django.apps import apps
        return apps.get_app_config(app_label).get_models()
    except ImportError:
        from django.db.models import get_models
        return get_models(app_label)


def get_models_for_app(app_label):
    """Returns the models in the given app."""
    try:
        # django >= 1.7
        from django.apps import apps
        return apps.get_app_config(app_label).get_models()
    except ImportError:
        from django.db.models import get_app, get_models
        return get_models(get_app(app_label))


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
