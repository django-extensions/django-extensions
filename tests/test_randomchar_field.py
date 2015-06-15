import mock
import string
import pytest

import django
from django.test import TestCase

from .testapp.models import (
    RandomCharTestModel,
    RandomCharTestModelLowercase,
    RandomCharTestModelUppercase,
    RandomCharTestModelAlpha,
    RandomCharTestModelDigits,
    RandomCharTestModelPunctuation,
    RandomCharTestModelLowercaseAlphaDigits,
    RandomCharTestModelUppercaseAlphaDigits,
)

if django.VERSION >= (1, 7):
    from django.db import migrations  # NOQA
    from django.db.migrations.writer import MigrationWriter  # NOQA
    from django.utils import six  # NOQA
    import django_extensions  # NOQA


class RandomCharFieldTest(TestCase):

    def testRandomCharField(self):
        m = RandomCharTestModel()
        m.save()
        assert len(m.random_char_field) == 8, m.random_char_field

    def testRandomCharFieldLowercase(self):
        m = RandomCharTestModelLowercase()
        m.save()
        for c in m.random_char_field:
            assert c.islower(), m.random_char_field

    def testRandomCharFieldUppercase(self):
        m = RandomCharTestModelUppercase()
        m.save()
        for c in m.random_char_field:
            assert c.isupper(), m.random_char_field

    def testRandomCharFieldAlpha(self):
        m = RandomCharTestModelAlpha()
        m.save()
        for c in m.random_char_field:
            assert c.isalpha(), m.random_char_field

    def testRandomCharFieldDigits(self):
        m = RandomCharTestModelDigits()
        m.save()
        for c in m.random_char_field:
            assert c.isdigit(), m.random_char_field

    def testRandomCharFieldPunctuation(self):
        m = RandomCharTestModelPunctuation()
        m.save()
        for c in m.random_char_field:
            assert c in string.punctuation, m.random_char_field

    def testRandomCharTestModelLowercaseAlphaDigits(self):
        m = RandomCharTestModelLowercaseAlphaDigits()
        m.save()
        for c in m.random_char_field:
            assert c.isdigit() or (c.isalpha() and c.islower()), m.random_char_field

    def testRandomCharTestModelUppercaseAlphaDigits(self):
        m = RandomCharTestModelUppercaseAlphaDigits()
        m.save()
        for c in m.random_char_field:
            assert c.isdigit() or (c.isalpha() and c.isupper()), m.random_char_field

    def testRandomCharTestModelDuplicate(self):
        m = RandomCharTestModel()
        m.save()
        with mock.patch('django_extensions.db.fields.RandomCharField.random_char_generator') as func:
            func.return_value = iter([m.random_char_field, 'aaa'])
            m = RandomCharTestModel()
            m.save()
        assert m.random_char_field == 'aaa'

    def testRandomCharTestModelAsserts(self):
        with mock.patch('django_extensions.db.fields.get_random_string') as mock_sample:
            mock_sample.return_value = 'aaa'
            m = RandomCharTestModel()
            m.save()

            m = RandomCharTestModel()
            with pytest.raises(RuntimeError):
                m.save()
