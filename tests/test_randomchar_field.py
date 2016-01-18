# coding=utf-8
import string

import mock
import pytest

from .testapp.models import (
    RandomCharTestModel, RandomCharTestModelAlpha, RandomCharTestModelDigits,
    RandomCharTestModelLowercase, RandomCharTestModelLowercaseAlphaDigits,
    RandomCharTestModelPunctuation, RandomCharTestModelUppercase,
    RandomCharTestModelUppercaseAlphaDigits,
)

pytestmark = pytest.mark.django_db


class TestRandomCharField:

    def testRandomCharField(self):
        m = RandomCharTestModel.objects.create()
        assert len(m.random_char_field) == 8, m.random_char_field

    @pytest.mark.parametrize(
        'model, checker',
        (
            (RandomCharTestModelLowercase, lambda c: c.islower()),
            (RandomCharTestModelUppercase, lambda c: c.isupper()),
            (RandomCharTestModelAlpha, lambda c: c.isalpha()),
            (RandomCharTestModelDigits, lambda c: c.isdigit()),
            (RandomCharTestModelPunctuation, lambda c: c in string.punctuation),
            (RandomCharTestModelLowercaseAlphaDigits, lambda c: c.isdigit() or (c.isalpha() and c.islower())),
            (RandomCharTestModelUppercaseAlphaDigits, lambda c: c.isdigit() or (c.isalpha() and c.isupper())),
        )
    )
    def test_string_generation(self, model, checker):
        instance = model.objects.create()
        for character in instance.random_char_field:
            assert checker(character), instance.random_char_field

    def testRandomCharTestModelDuplicate(self):
        m = RandomCharTestModel.objects.create()
        with mock.patch('django_extensions.db.fields.RandomCharField.random_char_generator') as func:
            func.return_value = iter([m.random_char_field, 'aaa'])
            m = RandomCharTestModel.objects.create()
        assert m.random_char_field == 'aaa'

    def testRandomCharTestModelAsserts(self):
        with mock.patch('django_extensions.db.fields.get_random_string') as mock_sample:
            mock_sample.return_value = 'aaa'
            RandomCharTestModel.objects.create()

            with pytest.raises(RuntimeError):
                RandomCharTestModel.objects.create()
