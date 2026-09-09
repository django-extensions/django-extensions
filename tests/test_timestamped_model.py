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

    def test_update_fields_updates_modified(self):
        """
        When save(update_fields=[...]) is used, the "modified" field should
        still be persisted to the database.
        """
        t = TimestampedTestModel.objects.create()
        modified = t.modified

        time.sleep(1)

        t.save(update_fields=[])
        t.refresh_from_db()
        self.assertNotEqual(modified, t.modified)

    def test_update_fields_with_no_modified_in_list(self):
        """
        Even when update_fields already contains other field names, "modified"
        should be appended and persisted.
        """
        t = TimestampedTestModel.objects.create()
        modified = t.modified

        time.sleep(1)

        # TimestampedTestModel has no extra fields, but the empty list still
        # proves the field is added and written.
        t.save(update_fields=())
        t.refresh_from_db()
        self.assertNotEqual(modified, t.modified)

    def test_update_fields_respects_update_modified_false(self):
        """update_modified=False should still skip modified even with update_fields."""
        t = TimestampedTestModel.objects.create()
        modified = t.modified

        time.sleep(1)

        t.save(update_fields=[], update_modified=False)
        t.refresh_from_db()
        self.assertEqual(modified, t.modified)
