import unittest

from django.conf import settings
from django.core.management import call_command
from django.db.models import loading
from django.db import models
from django_extensions.db.fields import AutoSlugField


class SluggedTestModel(models.Model):
    title = models.CharField(max_length=42)
    slug = AutoSlugField(populate_from='title')


class AutoSlugFieldTest(unittest.TestCase):
    def setUp(self):
        self.old_installed_apps = settings.INSTALLED_APPS
        settings.INSTALLED_APPS = list(settings.INSTALLED_APPS)
        settings.INSTALLED_APPS.append('django_extensions.tests')
        loading.cache.loaded = False
        call_command('syncdb', verbosity=0)

    def tearDown(self):
        SluggedTestModel.objects.all().delete()
        settings.INSTALLED_APPS = self.old_installed_apps

    def testAutoCreateSlug(self):
        m = SluggedTestModel(title='foo')
        m.save()
        self.assertEqual(m.slug, 'foo')

    def testAutoCreateNextSlug(self):
        m = SluggedTestModel(title='foo')
        m.save()

        m = SluggedTestModel(title='foo')
        m.save()
        self.assertEqual(m.slug, 'foo-2')

    def testAutoCreateSlugWithNumber(self):
        m = SluggedTestModel(title='foo 2012')
        m.save()
        self.assertEqual(m.slug, 'foo-2012')

    def testAutoUpdateSlugWithNumber(self):
        m = SluggedTestModel(title='foo 2012')
        m.save()
        m.save()
        self.assertEqual(m.slug, 'foo-2012')

    def testUpdateSlug(self):
        m = SluggedTestModel(title='foo')
        m.save()

        # update m instance without using `save'
        SluggedTestModel.objects.filter(pk=m.pk).update(slug='foo-2012')
        # update m instance with new data from the db
        m = SluggedTestModel.objects.get(pk=m.pk)

        self.assertEqual(m.slug, 'foo-2012')

        m.save()
        self.assertEqual(m.slug, 'foo-2012')
