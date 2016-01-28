# coding=utf-8
from django.test import TestCase

from .testapp.models import JSONFieldTestModel


class JsonFieldTest(TestCase):
    def test_char_field_create(self):
        j = JSONFieldTestModel.objects.create(a=6, j_field=dict(foo='bar'))
        self.assertEqual(j.a, 6)
        self.assertEqual(j.j_field, {'foo': 'bar'})

    def test_default(self):
        j = JSONFieldTestModel.objects.create(a=1)
        self.assertEqual(j.j_field, {})

    def test_empty_list(self):
        j = JSONFieldTestModel.objects.create(a=6, j_field=[])
        self.assertTrue(isinstance(j.j_field, list))
        self.assertEqual(j.j_field, [])

    def test_float_values(self):
        """ Tests that float values in JSONFields are correctly serialized over repeated saves.
            Regression test for c382398b, which fixes floats being returned as strings after a second save.
        """
        test_instance = JSONFieldTestModel(a=6, j_field={'test': 0.1})
        test_instance.save()

        test_instance = JSONFieldTestModel.objects.get()
        test_instance.save()

        test_instance = JSONFieldTestModel.objects.get()
        self.assertEqual(test_instance.j_field['test'], 0.1)
