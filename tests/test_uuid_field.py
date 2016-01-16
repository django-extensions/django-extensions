# coding=utf-8
import re
import uuid

import pytest
import six

from django_extensions.db.fields import PostgreSQLUUIDField

from .testapp.models import (
    UUIDTestAggregateModel, UUIDTestManyToManyModel, UUIDTestModel_field,
    UUIDTestModel_pk,
)

pytestmark = pytest.mark.django_db


class TestUUIDField:

    def test_UUID_field_create(self):
        j = UUIDTestModel_field.objects.create(a=6, uuid_field='550e8400-e29b-41d4-a716-446655440000')
        assert j.uuid_field == '550e8400-e29b-41d4-a716-446655440000'

    def test_UUID_field_pk_create(self):
        j = UUIDTestModel_pk.objects.create(uuid_field='550e8400-e29b-41d4-a716-446655440000')
        assert j.uuid_field == '550e8400-e29b-41d4-a716-446655440000'
        assert j.pk == '550e8400-e29b-41d4-a716-446655440000'

    def test_UUID_field_pk_aggregate_create(self):
        j = UUIDTestAggregateModel.objects.create(a=6, uuid_field='550e8400-e29b-41d4-a716-446655440001')
        assert j.a == 6
        assert isinstance(j.pk, six.string_types)
        assert len(j.pk) == 36

    def test_UUID_field_manytomany_create(self):
        j = UUIDTestManyToManyModel.objects.create(uuid_field='550e8400-e29b-41d4-a716-446655440010')
        assert j.uuid_field == '550e8400-e29b-41d4-a716-446655440010'
        assert j.pk == '550e8400-e29b-41d4-a716-446655440010'


class TestPostgreSQLUUIDField:

    def test_uuid_casting(self):
        # As explain by postgres documentation
        # http://www.postgresql.org/docs/9.1/static/datatype-uuid.html
        # an uuid needs to be a sequence of lower-case hexadecimal digits, in
        # several groups separated by hyphens, specifically a group of 8 digits
        # followed by three groups of 4 digits followed by a group of 12 digits
        matcher = re.compile('^[\da-f]{8}-[\da-f]{4}-[\da-f]{4}-[\da-f]{4}'
                             '-[\da-f]{12}$')
        field = PostgreSQLUUIDField()
        for value in (str(uuid.uuid4()), uuid.uuid4().urn, uuid.uuid4().hex,
                      uuid.uuid4().int, uuid.uuid4().bytes):
            prepared_value = field.get_db_prep_value(value, None)
            assert matcher.match(prepared_value) is not None, prepared_value
