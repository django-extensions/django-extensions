# coding=utf-8
import pytest

from .testapp.models import JSONFieldModel, InheritedFromConcreteJSONFieldModel, InheritedFromAbstractJSONFieldModel


pytestmark = pytest.mark.django_db


DEFAULT = {}


@pytest.mark.parametrize(
    'model', (
        JSONFieldModel,
        InheritedFromConcreteJSONFieldModel,
        InheritedFromAbstractJSONFieldModel
    )
)
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
def test_json_field_create(model, create_kwargs):
    expected = create_kwargs.get('field', DEFAULT)

    instance = model.objects.create(**create_kwargs)
    assert instance.field == expected

    from_db = model.objects.get()
    assert from_db.field == expected
