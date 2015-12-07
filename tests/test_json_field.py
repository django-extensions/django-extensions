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
