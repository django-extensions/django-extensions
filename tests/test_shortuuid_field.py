# coding=utf-8
import pytest
import six

from .testapp.models import (
    ShortUUIDTestAggregateModel, ShortUUIDTestManyToManyModel,
    ShortUUIDTestModel_field, ShortUUIDTestModel_pk,
)

pytestmark = pytest.mark.django_db


class TestShortUUIDField:

    def test_UUID_field_create(self):
        j = ShortUUIDTestModel_field.objects.create(a=6, uuid_field='vytxeTZskVKR7C7WgdSP3d')
        assert j.uuid_field == 'vytxeTZskVKR7C7WgdSP3d'

    def test_UUID_field_pk_create(self):
        j = ShortUUIDTestModel_pk.objects.create(uuid_field='vytxeTZskVKR7C7WgdSP3d')
        assert j.uuid_field == 'vytxeTZskVKR7C7WgdSP3d'
        assert j.pk == 'vytxeTZskVKR7C7WgdSP3d'

    def test_UUID_field_pk_aggregate_create(self):
        j = ShortUUIDTestAggregateModel.objects.create(a=6)
        assert j.a == 6
        assert isinstance(j.pk, six.string_types)
        assert len(j.pk) < 23

    def test_UUID_field_manytomany_create(self):
        j = ShortUUIDTestManyToManyModel.objects.create(uuid_field='vytxeTZskVKR7C7WgdSP3e')
        assert j.uuid_field == 'vytxeTZskVKR7C7WgdSP3e'
        assert j.pk == 'vytxeTZskVKR7C7WgdSP3e'
