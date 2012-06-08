import unittest

from django.db import connection
from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.db import models
from django_extensions.db.fields.json import JSONField


class TestModel(models.Model):
    a = models.IntegerField()
    j_field = JSONField()


class JsonFieldTest(unittest.TestCase):

    def setUp(self):
        self.old_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS.append('django_extensions.tests')
        loading.cache.loaded = False
        call_command('syncdb', verbosity=0)

    def tearDown(self):
        settings.INSTALLED_APPS = self.old_installed_apps

    def testCharFieldCreate(self):
        j = TestModel.objects.create(a=6, j_field=dict(foo='bar'))

    def testEmptyList(self):
        j = TestModel.objects.create(a=6, j_field=[])
        self.assertIsInstance(j.j_field, list)
        self.assertEquals(j.j_field, [])

