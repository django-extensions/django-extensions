import six
from .test_fields import FieldTestCase

from .testapp.models import ShortUUIDTestModel_field, ShortUUIDTestModel_pk, ShortUUIDTestAgregateModel, ShortUUIDTestManyToManyModel


class ShortUUIDFieldTest(FieldTestCase):
    def testUUIDFieldCreate(self):
        j = ShortUUIDTestModel_field.objects.create(a=6, uuid_field=six.u('vytxeTZskVKR7C7WgdSP3d'))
        self.assertEqual(j.uuid_field, six.u('vytxeTZskVKR7C7WgdSP3d'))

    def testUUIDField_pkCreate(self):
        j = ShortUUIDTestModel_pk.objects.create(uuid_field=six.u('vytxeTZskVKR7C7WgdSP3d'))
        self.assertEqual(j.uuid_field, six.u('vytxeTZskVKR7C7WgdSP3d'))
        self.assertEqual(j.pk, six.u('vytxeTZskVKR7C7WgdSP3d'))

    def testUUIDField_pkAgregateCreate(self):
        j = ShortUUIDTestAgregateModel.objects.create(a=6)
        self.assertEqual(j.a, 6)
        self.assertIsInstance(j.pk, six.string_types)
        self.assertTrue(len(j.pk) < 23)

    def testUUIDFieldManyToManyCreate(self):
        j = ShortUUIDTestManyToManyModel.objects.create(uuid_field=six.u('vytxeTZskVKR7C7WgdSP3e'))
        self.assertEqual(j.uuid_field, six.u('vytxeTZskVKR7C7WgdSP3e'))
        self.assertEqual(j.pk, six.u('vytxeTZskVKR7C7WgdSP3e'))
