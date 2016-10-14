# -*- coding: utf-8 -*-
import time
from django.test import TestCase

from .testapp.models import TimestampedTestModel


class ModifiedFieldTest(TestCase):
    def test_update(self):
        t = TimestampedTestModel.objects.create()
        modified = t.modified

        time.sleep(1)

        t.save()
        self.assertNotEqual(modified, t.modified)

    def test_update_no_modified(self):
        t = TimestampedTestModel.objects.create()
        modified = t.modified

        time.sleep(1)

        t.save(update_modified=False)
        self.assertEqual(modified, t.modified)
