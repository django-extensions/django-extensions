# coding=utf-8
import pytest

from .testapp.models import JSONFieldTestModel


pytestmark = pytest.mark.django_db


DEFAULT = {}


@pytest.mark.parametrize(
    'create_kwargs',
    (
        DEFAULT,
        {'field': {'foo': 'bar'}},
        {'field': []},
        {'field': [1, 2, 3]},
        {'field': None},
        {'field': True},
        {'field': 'foo'},
    )
)
def test_json_field_create(create_kwargs):
    expected = create_kwargs.get('field', DEFAULT)

    instance = JSONFieldTestModel.objects.create(**create_kwargs)
    assert instance.field == expected

    from_db = JSONFieldTestModel.objects.get()
    assert from_db.field == expected
