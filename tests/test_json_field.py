# -*- coding: utf-8 -*-
from django.test import TestCase

from .testapp.models import JSONFieldTestModel
from django_extensions.db.fields.json import (
    dumps,
    loads,
    JSONField,
    JSONDict,
    JSONList
)


class JsonFieldTest(TestCase):
    def test_char_field_create(self):
        j = JSONFieldTestModel.objects.create(a=6, j_field=dict(foo='bar'))
        self.assertEqual(j.a, 6)
        self.assertEqual(j.j_field, {'foo': 'bar'})

    def test_char_field_get_or_create(self):
        j, created = JSONFieldTestModel.objects.get_or_create(
            a=6, j_field=dict(foo='bar'))

        self.assertTrue(created)
        self.assertEqual(j.a, 6)
        self.assertEqual(j.j_field, {'foo': 'bar'})

        j, created = JSONFieldTestModel.objects.get_or_create(a=6, j_field=dict(foo='bar'))

        self.assertFalse(created)
        self.assertEqual(j.a, 6)
        self.assertEqual(j.j_field, {'foo': 'bar'})

    def test_default(self):
        j = JSONFieldTestModel.objects.create(a=1)
        self.assertEqual(j.j_field, {})

    def test_default_mutable(self):
        j1 = JSONFieldTestModel.objects.create(a=1)
        self.assertEqual(j1.j_field, {})

        j2 = JSONFieldTestModel.objects.create(a=1)
        self.assertEqual(j2.j_field, {})

        self.assertIsNot(j1.j_field, j2.j_field)

    def test_get_default(self):
        j_field = JSONField()
        value = j_field.get_default()
        self.assertEqual(value, {})
        self.assertIsInstance(value, JSONDict)

        j_field = JSONField(default={})
        value = j_field.get_default()
        self.assertEqual(value, {})
        self.assertIsInstance(value, JSONDict)

        j_field = JSONField(default='{}')
        value = j_field.get_default()
        self.assertEqual(value, {})
        self.assertIsInstance(value, JSONDict)

        j_field = JSONField(default=[{}])
        value = j_field.get_default()
        self.assertEqual(value, [{}])
        self.assertIsInstance(value, JSONList)

        j_field = JSONField(default='[{}]')
        value = j_field.get_default()
        self.assertEqual(value, [{}])
        self.assertIsInstance(value, JSONList)

        j_field = JSONField(default=lambda: '{}')
        value = j_field.get_default()
        self.assertEqual(value, {})
        self.assertIsInstance(value, JSONDict)

    def test_empty_list(self):
        j = JSONFieldTestModel.objects.create(a=6, j_field=[])
        self.assertIsInstance(j.j_field, list)
        self.assertEqual(j.j_field, [])

    def test_float_values(self):
        """Tests that float values in JSONFields are correctly serialized over
        repeated saves. Regression test for c382398b, which fixes floats
        being returned as strings after a second save."""

        test_instance = JSONFieldTestModel(a=6, j_field={'test': 0.1})
        test_instance.save()

        test_instance = JSONFieldTestModel.objects.get()
        test_instance.save()

        test_instance = JSONFieldTestModel.objects.get()
        self.assertEqual(test_instance.j_field['test'], 0.1)

    def test_get_prep_value(self):
        j_field = JSONField()

        self.assertEqual(
            str(dumps([{'a': 'a'}])),
            j_field.get_prep_value(value=[{'a': 'a'}]),
        )

        self.assertEqual(
            str(dumps([{'a': 'a'}])),
            j_field.get_prep_value(value='[{"a": "a"}]'),
        )

    def test_get_db_prep_save(self):
        j_field = JSONField()

        self.assertEqual(
            str(dumps([{'a': 'a'}])),
            j_field.get_db_prep_save(value=[{'a': 'a'}], connection=None),
        )

        self.assertEqual(
            str('[{"a": "a"}]'),
            j_field.get_db_prep_save(value='[{"a": "a"}]', connection=None),
        )

    def test_to_python(self):
        j_field = JSONField()

        self.assertEqual(
            loads('1'),
            j_field.to_python('1')
        )

        self.assertEqual(
            loads('"1"'),
            j_field.to_python('"1"')
        )

        self.assertEqual(
            loads('[{"a": 1}]'),
            j_field.to_python('[{"a": 1}]')
        )

        self.assertEqual(
            loads('[{"a": "1"}]'),
            j_field.to_python('[{"a": "1"}]')
        )
