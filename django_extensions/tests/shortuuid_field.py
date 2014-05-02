import six
from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.utils import unittest

from django_extensions.tests.testapp.models import ShortUUIDTestModel_field, ShortUUIDTestModel_pk, ShortUUIDTestAgregateModel, ShortUUIDTestManyToManyModel


class ShortUUIDFieldTest(unittest.TestCase):
    def setUp(self):
        self.old_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS.append('django_extensions.tests')
        loading.cache.loaded = False
        call_command('syncdb', verbosity=0)

    def tearDown(self):
        settings.INSTALLED_APPS = self.old_installed_apps

    def testUUIDFieldCreate(self):
        j = ShortUUIDTestModel_field.objects.create(a=6, uuid_field=six.u('vytxeTZskVKR7C7WgdSP3d'))
        self.assertEqual(j.uuid_field, six.u('vytxeTZskVKR7C7WgdSP3d'))

    def testUUIDField_pkCreate(self):
        j = ShortUUIDTestModel_pk.objects.create(uuid_field=six.u('vytxeTZskVKR7C7WgdSP3d'))
        self.assertEqual(j.uuid_field, six.u('vytxeTZskVKR7C7WgdSP3d'))
        self.assertEqual(j.pk, six.u('vytxeTZskVKR7C7WgdSP3d'))

    def testUUIDField_pkAgregateCreate(self):
        j = ShortUUIDTestAgregateModel.objects.create(a=6)
        self.assertEqual(j.a, 6)
        self.assertIsInstance(j.pk, six.string_types)
        self.assertTrue(len(j.pk) < 23)

    def testUUIDFieldManyToManyCreate(self):
        j = ShortUUIDTestManyToManyModel.objects.create(uuid_field=six.u('vytxeTZskVKR7C7WgdSP3e'))
        self.assertEqual(j.uuid_field, six.u('vytxeTZskVKR7C7WgdSP3e'))
        self.assertEqual(j.pk, six.u('vytxeTZskVKR7C7WgdSP3e'))
