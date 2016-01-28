# coding=utf-8
import pytest

from django_extensions.db.fields.json import JSONField
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


def test_float_values():
    """ Tests that float values in JSONFields are correctly serialized over repeated saves.
        Regression test for c382398b, which fixes floats being returned as strings after a second save.
    """
    test_instance = JSONFieldModel.objects.create(a=6, field={'test': 0.1})

    test_instance = JSONFieldModel.objects.get()
    test_instance.save()

    test_instance = JSONFieldModel.objects.get()
    assert test_instance.field['test'] ==  0.1


@pytest.mark.parametrize(
    'value, expected',
    (
        ([{'a': 'a'}], dumps([{'a': 'a'}])),
        ('[{"a": "a"}]', '[{"a": "a"}]'),
    )
)
def test_get_db_prep_save(value, expected):
    assert JSONField().get_db_prep_save(value=value, connection=None) == expected
