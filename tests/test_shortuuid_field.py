# -*- coding: utf-8 -*-

from django.test import TestCase

from .testapp.models import (
    ShortUUIDTestAgregateModel, ShortUUIDTestManyToManyModel,
    ShortUUIDTestModel_field, ShortUUIDTestModel_pk,
)


class ShortUUIDFieldTest(TestCase):
    def test_UUID_field_create(self):
        j = ShortUUIDTestModel_field.objects.create(a=6, uuid_field='vytxeTZskVKR7C7WgdSP3d')
        self.assertEqual(j.uuid_field, 'vytxeTZskVKR7C7WgdSP3d')

    def test_UUID_field_pk_create(self):
        j = ShortUUIDTestModel_pk.objects.create(uuid_field='vytxeTZskVKR7C7WgdSP3d')
        self.assertEqual(j.uuid_field, 'vytxeTZskVKR7C7WgdSP3d')
        self.assertEqual(j.pk, 'vytxeTZskVKR7C7WgdSP3d')

    def test_UUID_field_pk_agregate_create(self):
        j = ShortUUIDTestAgregateModel.objects.create(a=6)
        self.assertEqual(j.a, 6)
        self.assertIsInstance(j.pk, str)
        self.assertTrue(len(j.pk) < 23)

    def test_UUID_field_manytomany_create(self):
        j = ShortUUIDTestManyToManyModel.objects.create(uuid_field='vytxeTZskVKR7C7WgdSP3e')
        self.assertEqual(j.uuid_field, 'vytxeTZskVKR7C7WgdSP3e')
        self.assertEqual(j.pk, 'vytxeTZskVKR7C7WgdSP3e')
