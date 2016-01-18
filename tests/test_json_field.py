# coding=utf-8
import pytest

from .testapp.models import JSONFieldTestModel

pytestmark = pytest.mark.django_db


class TestJsonField:

    def test_char_field_create(self):
        j = JSONFieldTestModel.objects.create(a=6, j_field={'foo': 'bar'})
        assert j.a == 6
        assert j.j_field == {'foo': 'bar'}

    def test_default(self):
        j = JSONFieldTestModel.objects.create(a=1)
        assert j.j_field == {}

    def test_empty_list(self):
        j = JSONFieldTestModel.objects.create(a=6, j_field=[])
        assert isinstance(j.j_field, list)
        assert j.j_field == []
