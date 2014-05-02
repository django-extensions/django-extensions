from django_extensions.tests.fields import FieldTestCase
from django_extensions.tests.testapp.models import JSONFieldTestModel


class JsonFieldTest(FieldTestCase):
    def testCharFieldCreate(self):
        j = JSONFieldTestModel.objects.create(a=6, j_field=dict(foo='bar'))
        self.assertEqual(j.a, 6)

    def testDefault(self):
        j = JSONFieldTestModel.objects.create(a=1)
        self.assertEqual(j.j_field, {})

    def testEmptyList(self):
        j = JSONFieldTestModel.objects.create(a=6, j_field=[])
        self.assertTrue(isinstance(j.j_field, list))
        self.assertEqual(j.j_field, [])
