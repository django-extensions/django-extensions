import pytest

import django
from django.conf import settings
from django.core.management import call_command
from django.test import TestCase

if django.VERSION >= (1, 7):
    from django.db import migrations  # NOQA
    from django.db import models  # NOQA
    from django.db.migrations.writer import MigrationWriter  # NOQA
    from django.utils import six  # NOQA
    import django_extensions  # NOQA

@pytest.mark.usefixtures("admin_user")
class FieldTestCase(TestCase):
    """A Django TestCase with an admin user"""
    pass
