# -*- coding: utf-8 -*-
import pytest
import django
from django.db import migrations, models
from django.db.migrations.writer import MigrationWriter
from django.test import TestCase
from django.utils import six
from django.utils.encoding import force_bytes

import django_extensions  # noqa
from django_extensions.db.fields import AutoSlugField

from .testapp.models import ChildSluggedTestModel, SluggedTestModel, \
    FKSluggedTestModel, FKSluggedTestModelCallable, \
    ModelMethodSluggedTestModel


@pytest.mark.usefixtures("admin_user")
class AutoSlugFieldTest(TestCase):
    def tearDown(self):
        super(AutoSlugFieldTest, self).tearDown()

        SluggedTestModel.objects.all().delete()

    def test_auto_create_slug(self):
        m = SluggedTestModel(title='foo')
        m.save()
        self.assertEqual(m.slug, 'foo')

    def test_auto_create_next_slug(self):
        m = SluggedTestModel(title='foo')
        m.save()

        m = SluggedTestModel(title='foo')
        m.save()
        self.assertEqual(m.slug, 'foo-2')

    def test_auto_create_slug_with_number(self):
        m = SluggedTestModel(title='foo 2012')
        m.save()
        self.assertEqual(m.slug, 'foo-2012')

    def test_auto_update_slug_with_number(self):
        m = SluggedTestModel(title='foo 2012')
        m.save()
        m.save()
        self.assertEqual(m.slug, 'foo-2012')

    def test_update_slug(self):
        m = SluggedTestModel(title='foo')
        m.save()
        self.assertEqual(m.slug, 'foo')

        # update m instance without using `save'
        SluggedTestModel.objects.filter(pk=m.pk).update(slug='foo-2012')
        # update m instance with new data from the db
        m = SluggedTestModel.objects.get(pk=m.pk)
        self.assertEqual(m.slug, 'foo-2012')

        m.save()
        self.assertEqual(m.title, 'foo')
        self.assertEqual(m.slug, 'foo-2012')

        # Check slug is not overwrite
        m.title = 'bar'
        m.save()
        self.assertEqual(m.title, 'bar')
        self.assertEqual(m.slug, 'foo-2012')

    def test_simple_slug_source(self):
        m = SluggedTestModel(title='-foo')
        m.save()
        self.assertEqual(m.slug, 'foo')

        n = SluggedTestModel(title='-foo')
        n.save()
        self.assertEqual(n.slug, 'foo-2')

        n.save()
        self.assertEqual(n.slug, 'foo-2')

    def test_empty_slug_source(self):
        # regression test

        m = SluggedTestModel(title='')
        m.save()
        self.assertEqual(m.slug, '-2')

        n = SluggedTestModel(title='')
        n.save()
        self.assertEqual(n.slug, '-3')

        n.save()
        self.assertEqual(n.slug, '-3')

    def test_callable_slug_source(self):
        m = ModelMethodSluggedTestModel(title='-foo')
        m.save()
        self.assertEqual(m.slug, 'the-title-is-foo')

        n = ModelMethodSluggedTestModel(title='-foo')
        n.save()
        self.assertEqual(n.slug, 'the-title-is-foo-2')

        n.save()
        self.assertEqual(n.slug, 'the-title-is-foo-2')

    def test_inheritance_creates_next_slug(self):
        m = SluggedTestModel(title='foo')
        m.save()

        n = ChildSluggedTestModel(title='foo')
        n.save()
        self.assertEqual(n.slug, 'foo-2')

        o = SluggedTestModel(title='foo')
        o.save()
        self.assertEqual(o.slug, 'foo-3')

    def test_foreign_key_populate_from_field(self):
        m_fk = SluggedTestModel(title='foo')
        m_fk.save()
        m = FKSluggedTestModel(related_field=m_fk)
        m.save()
        self.assertEqual(m.slug, 'foo')

    def test_foreign_key_populate_from_callable(self):
        m_fk = ModelMethodSluggedTestModel(title='foo')
        m_fk.save()
        m = FKSluggedTestModelCallable(related_field=m_fk)
        m.save()
        self.assertEqual(m.slug, 'the-title-is-foo')


class MigrationTest(TestCase):
    def safe_exec(self, string, value=None):
        dct = {}
        try:
            exec(force_bytes(string), globals(), dct)
        except Exception as e:
            if value:
                self.fail("Could not exec %r (from value %r): %s" % (string.strip(), value, e))
            else:
                self.fail("Could not exec %r: %s" % (string.strip(), e))
        return dct

    def test_17_migration(self):
        """
        Tests making migrations with Django's migration framework
        """

        fields = {
            'autoslugfield': AutoSlugField(populate_from='otherfield'),
        }

        migration = type(str("Migration"), (migrations.Migration,), {
            "operations": [
                migrations.CreateModel("MyModel", tuple(fields.items()),
                                       {'populate_from': 'otherfield'},
                                       (models.Model,)),
            ],
        })
        writer = MigrationWriter(migration)
        output = writer.as_string()
        # It should NOT be unicode.
        if django.VERSION < (1, 11):
            self.assertIsInstance(output, six.binary_type, "Migration as_string returned unicode")
        else:
            # As of Django 1.11 MigrationWriter.as_string returns unicode not bytes
            self.assertIsInstance(output, six.text_type, "Migration as_string returned bytes")
        # We don't test the output formatting - that's too fragile.
        # Just make sure it runs for now, and that things look alright.
        result = self.safe_exec(output)
        self.assertIn("Migration", result)
