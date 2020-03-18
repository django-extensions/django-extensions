# -*- coding: utf-8 -*-
from datetime import datetime

from django.test import TestCase

from .testapp.models import (
    ModelModificationDateTimeField,
    CustomModelModificationDateTimeField,
    DisabledUpdateModelModificationDateTimeField,
)


class ModificationDatetimeFieldTest(TestCase):
    def test_update_model_with_modification_field(self):
        m = ModelModificationDateTimeField.objects.create()
        current_updated_time = m.modified
        m.field_to_update = False
        m.save()
        self.assertNotEqual(m.modified, current_updated_time)

    def test_custom_modification_field_name(self):
        m = CustomModelModificationDateTimeField.objects.create()
        current_updated_time = m.custom_modified
        m.field_to_update = False
        m.save()
        self.assertNotEqual(m.custom_modified, current_updated_time)

    def test_disabled_update_modification_field(self):
        m = DisabledUpdateModelModificationDateTimeField.objects.create(modified=datetime.now())
        current_updated_time = m.modified
        m.field_to_update = False
        m.save()
        self.assertEqual(m.modified, current_updated_time)
