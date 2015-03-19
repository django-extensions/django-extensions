from __future__ import unicode_literals

import sys

import django
from django.conf import settings

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
        return settings.INSTALLED_APPS
