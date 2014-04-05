import six
from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.db import models
from django.utils import unittest

from django_extensions.db.fields import ShortUUIDField


class TestModel_suuid_field(models.Model):
    a = models.IntegerField()
    uuid_field = ShortUUIDField()


class TestModel_suuid_pk(models.Model):
    uuid_field = ShortUUIDField(primary_key=True)


class TestAgregateModel_suuid(TestModel_suuid_pk):
    a = models.IntegerField()


class TestManyToManyModel_suuid(TestModel_suuid_pk):
    many = models.ManyToManyField(TestModel_suuid_field)


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
        j = TestModel_suuid_field.objects.create(a=6, uuid_field=six.u('vytxeTZskVKR7C7WgdSP3d'))
        self.assertEqual(j.uuid_field, six.u('vytxeTZskVKR7C7WgdSP3d'))

    def testUUIDField_pkCreate(self):
        j = TestModel_suuid_pk.objects.create(uuid_field=six.u('vytxeTZskVKR7C7WgdSP3d'))
        self.assertEqual(j.uuid_field, six.u('vytxeTZskVKR7C7WgdSP3d'))
        self.assertEqual(j.pk, six.u('vytxeTZskVKR7C7WgdSP3d'))

    def testUUIDField_pkAgregateCreate(self):
        j = TestAgregateModel_suuid.objects.create(a=6)
        self.assertEqual(j.a, 6)
        self.assertIsInstance(j.pk, six.string_types)
        self.assertTrue(len(j.pk) < 23)

    def testUUIDFieldManyToManyCreate(self):
        j = TestManyToManyModel_suuid.objects.create(uuid_field=six.u('vytxeTZskVKR7C7WgdSP3e'))
        self.assertEqual(j.uuid_field, six.u('vytxeTZskVKR7C7WgdSP3e'))
        self.assertEqual(j.pk, six.u('vytxeTZskVKR7C7WgdSP3e'))
