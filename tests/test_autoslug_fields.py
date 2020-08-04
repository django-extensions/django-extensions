# -*- coding: utf-8 -*-
import pytest

from django.db import migrations, models
from django.db.migrations.writer import MigrationWriter
from django.test import TestCase
from django.utils.encoding import force_bytes

import django_extensions  # noqa
from django_extensions.db.fields import AutoSlugField

from .testapp.models import (
    ChildSluggedTestModel, CustomFuncPrecedenceSluggedTestModel, CustomFuncSluggedTestModel,
    FKSluggedTestModel, FKSluggedTestModelCallable, FunctionSluggedTestModel,
    ModelMethodSluggedTestModel, SluggedTestModel, SluggedTestNoOverwriteOnAddModel,
    OverridedFindUniqueModel, SluggedWithConstraintsTestModel,
    SluggedWithUniqueTogetherTestModel,
)


@pytest.mark.usefixtures("admin_user")
class AutoSlugFieldTest(TestCase):
    def tearDown(self):
        super().tearDown()

        SluggedTestModel.objects.all().delete()
        CustomFuncSluggedTestModel.objects.all().delete()
        CustomFuncPrecedenceSluggedTestModel.objects.all().delete()

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

    def test_callable_method_slug_source(self):
        m = ModelMethodSluggedTestModel(title='-foo')
        m.save()
        self.assertEqual(m.slug, 'the-title-is-foo')

        n = ModelMethodSluggedTestModel(title='-foo')
        n.save()
        self.assertEqual(n.slug, 'the-title-is-foo-2')

        n.save()
        self.assertEqual(n.slug, 'the-title-is-foo-2')

    def test_callable_function_slug_source(self):
        m = FunctionSluggedTestModel(title='-foo')
        m.save()
        self.assertEqual(m.slug, 'the-title-is-foo')

        n = FunctionSluggedTestModel(title='-foo')
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

    def test_copy_model_generates_new_slug(self):
        m = SluggedTestModel(title='foo')
        m.save()
        self.assertEqual(m.slug, 'foo')

        m.pk = None
        m.save()
        self.assertEqual(m.slug, 'foo-2')

    def test_copy_model_generates_new_slug_no_overwrite_on_add(self):
        m = SluggedTestNoOverwriteOnAddModel(title='foo')
        m.save()
        self.assertEqual(m.slug, 'foo')

        m.pk = None
        m.slug = None
        m.save()
        self.assertEqual(m.slug, 'foo-2')

    def test_populate_from_does_not_allow_bytes(self):
        with pytest.raises(TypeError):
            AutoSlugField(populate_from=b'bytes')

        with pytest.raises(TypeError):
            AutoSlugField(populate_from=[b'bytes'])

    def test_populate_from_must_allow_string_or_list_str_or_tuple_str(self):
        AutoSlugField(populate_from='str')
        AutoSlugField(populate_from=['str'])
        AutoSlugField(populate_from=('str', ))

    def test_slug_argument_priority(self):
        m = SluggedTestModel(slug='slug', title='title')
        m.save()
        self.assertEqual(m.slug, 'title')

    def test_slug_argument_priority_no_overwrite_on_add(self):
        m = SluggedTestNoOverwriteOnAddModel(slug='slug', title='title')
        m.save()
        self.assertEqual(m.slug, 'slug')

    def test_overrided_find_unique_autoslug_field(self):
        m = OverridedFindUniqueModel(title='foo')
        slug_field = m._meta.fields[2]
        self.assertFalse(hasattr(slug_field, 'overrided'))
        m.save()
        slug_field = m._meta.fields[2]
        self.assertTrue(slug_field.overrided)

    def test_slugify_func(self):
        to_upper = lambda c: c.upper()
        to_lower = lambda c: c.lower()

        content_n_func_n_expected = (
            ('test', to_upper, 'TEST'),
            ('', to_upper, ''),
            ('TEST', to_lower, 'test'),
        )

        for content, slugify_function, expected in content_n_func_n_expected:
            self.assertEqual(
                AutoSlugField.slugify_func(content, slugify_function),
                expected
            )

    def test_use_custom_slug_function(self):
        m = CustomFuncSluggedTestModel(title='test')
        m.save()
        self.assertEqual(m.slug, 'TEST')

    def test_precedence_custom_slug_function(self):
        m = CustomFuncPrecedenceSluggedTestModel(title='test')
        m.save()
        self.assertEqual(m.slug, 'TEST')
        self.assertTrue(hasattr(m._meta.get_field('slug'), 'slugify_function'))
        self.assertEqual(m._meta.get_field('slug').slugify_function('TEST'), 'test')

    def test_auto_create_slug_with_unique_together(self):
        m = SluggedWithUniqueTogetherTestModel(title='foo', category='self-introduction')
        m.save()
        self.assertEqual(m.slug, 'foo')

        m = SluggedWithUniqueTogetherTestModel(title='foo', category='review')
        m.save()
        self.assertEqual(m.slug, 'foo')

        # check if satisfy database integrity
        m = SluggedWithUniqueTogetherTestModel(title='foo', category='review')
        m.save()
        self.assertEqual(m.slug, 'foo-2')

    def test_auto_create_slug_with_constraints(self):
        m = SluggedWithConstraintsTestModel(title='foo', category='self-introduction')
        m.save()
        self.assertEqual(m.slug, 'foo')

        m = SluggedWithConstraintsTestModel(title='foo', category='review')
        m.save()
        self.assertEqual(m.slug, 'foo')

        # check if satisfy database integrity
        m = SluggedWithConstraintsTestModel(title='foo', category='review')
        m.save()
        self.assertEqual(m.slug, 'foo-2')


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
                migrations.CreateModel(
                    "MyModel",
                    tuple(fields.items()),
                    {'populate_from': 'otherfield'},
                    (models.Model,)
                ),
            ],
        })
        writer = MigrationWriter(migration)
        output = writer.as_string()

        self.assertIsInstance(output, str, "Migration as_string returned bytes")

        # We don't test the output formatting - that's too fragile.
        # Just make sure it runs for now, and that things look alright.
        result = self.safe_exec(output)
        self.assertIn("Migration", result)

    def test_stable_deconstruct(self):
        slug_field = SluggedTestModel._meta.get_field('slug')
        construction_values = slug_field.deconstruct()
        m = SluggedTestModel(title='foo')
        m.save()
        self.assertEqual(slug_field.deconstruct(), construction_values)
