# coding=utf-8
import pytest

from .testapp.models import (
    InheritedFromAbstractModel, InheritedFromConcreteModel, JSONFieldModel,
    NullableJSONFieldModel,
)

pytestmark = pytest.mark.django_db


DEFAULT = {}


@pytest.mark.parametrize(
    'model', (
        JSONFieldModel,
        InheritedFromConcreteModel,
        InheritedFromAbstractModel,
        NullableJSONFieldModel,
    )
)
@pytest.mark.parametrize(
    'create_kwargs',
    (
        DEFAULT,
        {'field': {'foo': 'bar'}},
        {'field': []},
        {'field': [1, 2, 3]},
        {'field': True},
        {'field': 'foo'},
        {'field': ''},
    )
)
def test_json_field_create(model, create_kwargs):
    expected = create_kwargs.get('field', DEFAULT)

    instance = model.objects.create(**create_kwargs)
    assert instance.field == expected

    from_db = model.objects.get()
    assert from_db.field == expected


@pytest.mark.parametrize(
    'model, expected',
    (
        (JSONFieldModel, {}),
        (NullableJSONFieldModel, None),
    )
)
def test_default_value(model, expected):
    instance = model.objects.create(field=None)
    assert instance.field == expected
    from_db = model.objects.get()
    assert from_db.field == expected
