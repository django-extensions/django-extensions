# -*- coding: utf-8 -*-
import string
import pytest

from django.test import TestCase

from .testapp.models import RandomCharTestModel, RandomCharTestModelUnique, RandomCharTestModelLowercase
from .testapp.models import RandomCharTestModelUppercase, RandomCharTestModelAlpha, RandomCharTestModelDigits
from .testapp.models import RandomCharTestModelPunctuation, RandomCharTestModelLowercaseAlphaDigits, RandomCharTestModelUppercaseAlphaDigits
from .testapp.models import RandomCharTestModelUniqueTogether

from unittest import mock


class RandomCharFieldTest(TestCase):

    def testRandomCharField(self):
        m = RandomCharTestModel()
        m.save()
        assert len(m.random_char_field) == 8, m.random_char_field

    def testRandomCharFieldUnique(self):
        m = RandomCharTestModelUnique()
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
        m = RandomCharTestModelUnique()
        m.save()
        with mock.patch('django_extensions.db.fields.RandomCharField.random_char_generator') as func:
            func.return_value = iter([m.random_char_field, 'aaa'])
            m = RandomCharTestModelUnique()
            m.save()
        assert m.random_char_field == 'aaa'

    def testRandomCharTestModelAsserts(self):
        with mock.patch('django_extensions.db.fields.get_random_string') as mock_sample:
            mock_sample.return_value = 'aaa'
            m = RandomCharTestModelUnique()
            m.save()

            m = RandomCharTestModelUnique()
            with pytest.raises(RuntimeError):
                m.save()

    def testRandomCharTestModelUniqueTogether(self):
        with mock.patch('django_extensions.db.fields.get_random_string') as mock_sample:
            mock_sample.return_value = 'aaa'
            m = RandomCharTestModelUniqueTogether()
            m.common_field = 'bbb'
            m.save()

            m = RandomCharTestModelUniqueTogether()
            m.common_field = 'bbb'
            with pytest.raises(RuntimeError):
                m.save()
