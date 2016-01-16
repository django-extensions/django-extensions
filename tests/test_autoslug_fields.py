# coding=utf-8
import django
import pytest
from django.db import models

from django_extensions.db.fields import AutoSlugField

from .testapp.models import ChildSluggedTestModel, SluggedTestModel

if django.VERSION >= (1, 7):
    from django.db import migrations  # NOQA
    from django.db.migrations.writer import MigrationWriter  # NOQA
    from django.utils import six  # NOQA
    import django_extensions  # NOQA


pytestmark = pytest.mark.django_db


class TestAutoSlugField:

    def test_auto_create_slug(self):
        m = SluggedTestModel.objects.create(title='foo')
        assert m.slug == 'foo'

    def test_auto_create_next_slug(self):
        SluggedTestModel.objects.create(title='foo')
        m = SluggedTestModel.objects.create(title='foo')
        assert m.slug == 'foo-2'

    def test_auto_create_slug_with_number(self):
        m = SluggedTestModel.objects.create(title='foo 2012')
        assert m.slug == 'foo-2012'

    def test_auto_update_slug_with_number(self):
        m = SluggedTestModel.objects.create(title='foo 2012')
        m.save()
        assert m.slug == 'foo-2012'

    def test_update_slug(self):
        m = SluggedTestModel.objects.create(title='foo')
        assert m.slug == 'foo'

        # update m instance without using `save'
        SluggedTestModel.objects.filter(pk=m.pk).update(slug='foo-2012')
        # update m instance with new data from the db
        m = SluggedTestModel.objects.get(pk=m.pk)
        assert m.slug == 'foo-2012'

        m.save()
        assert m.title == 'foo'
        assert m.slug == 'foo-2012'

        # Check slug is not overwrite
        m.title = 'bar'
        m.save()
        assert m.title == 'bar'
        assert m.slug == 'foo-2012'

    def test_simple_slug_source(self):
        m = SluggedTestModel.objects.create(title='-foo')
        assert m.slug == 'foo'

        n = SluggedTestModel.objects.create(title='-foo')
        assert n.slug == 'foo-2'

        n.save()
        assert n.slug == 'foo-2'

    def test_empty_slug_source(self):
        # regression test

        m = SluggedTestModel.objects.create(title='')
        assert m.slug == '-2'

        n = SluggedTestModel.objects.create(title='')
        assert n.slug == '-3'

        n.save()
        assert n.slug == '-3'

    def test_inheritance_creates_next_slug(self):
        SluggedTestModel.objects.create(title='foo')

        n = ChildSluggedTestModel.objects.create(title='foo')
        assert n.slug == 'foo-2'

        o = SluggedTestModel.objects.create(title='foo')
        assert o.slug == 'foo-3'


@pytest.mark.skipif(django.VERSION < (1, 7),
                    reason="Migrations are handled by south in Django <1.7")
class TestMigration:

    def safe_exec(self, string, value=None):
        l = {}
        try:
            exec(string, globals(), l)
        except Exception as e:
            if value:
                pytest.fail("Could not exec %r (from value %r): %s" % (string.strip(), value, e))
            else:
                pytest.fail("Could not exec %r: %s" % (string.strip(), e))
        return l

    def test_17_migration(self):
        """
        Tests making migrations with Django 1.7+'s migration framework
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
        assert isinstance(output, six.binary_type), "Migration as_string returned unicode"
        # We don't test the output formatting - that's too fragile.
        # Just make sure it runs for now, and that things look alright.
        result = self.safe_exec(output)
        assert "Migration" in result
