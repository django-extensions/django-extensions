from django.test import TestCase

from tests.testapp.models import IterDeleteModel
from django_extensions.db.models import IterativeDeleteErrorAction


class TestIterativeDelete(TestCase):
    def setUp(self):
        IterDeleteModel.deleted_by_instance_delete = 0
        IterDeleteModel.objects.bulk_create(
            [IterDeleteModel(name=f"obj-{i}") for i in range(3)]
        )

    def test_iterative_delete_calls_instance_delete(self):
        count, details = IterDeleteModel.objects.all().iterative_delete()
        assert count == 3
        assert isinstance(details, dict)
        # Each instance delete should have been invoked
        assert IterDeleteModel.deleted_by_instance_delete == 3

    def test_queryset_delete_default_iterative(self):
        IterDeleteModel.deleted_by_instance_delete = 0
        IterDeleteModel.objects.bulk_create(
            [IterDeleteModel(name=f"obj-{i}") for i in range(5)]
        )
        count, _ = IterDeleteModel.objects.filter(name__startswith="obj-").delete()
        assert count == 5
        assert IterDeleteModel.deleted_by_instance_delete == 5

    def test_queryset_delete_non_iterative_bulk(self):
        IterDeleteModel.deleted_by_instance_delete = 0
        IterDeleteModel.objects.bulk_create(
            [IterDeleteModel(name=f"obj-{i}") for i in range(2)]
        )
        # Opt into bulk delete should not call per-instance delete()
        IterDeleteModel.objects.all().delete(non_iterative=True)
        assert IterDeleteModel.deleted_by_instance_delete == 0


from tests.testapp.models import IterDeleteFailModel


class TestIterativeDeleteErrors(TestCase):
    def setUp(self):
        IterDeleteFailModel.objects.all().delete(non_iterative=True)

    def test_collect_exceptions_continues_and_reports(self):
        IterDeleteFailModel.objects.bulk_create(
            [
                IterDeleteFailModel(name="ok-1"),
                IterDeleteFailModel(name="bad-1"),
                IterDeleteFailModel(name="ok-2"),
            ]
        )
        count, details = IterDeleteFailModel.objects.all().iterative_delete(
            collect_exceptions=True
        )
        assert count == 2
        assert isinstance(details, dict)
        assert "__errors__" in details
        assert len(details["__errors__"]) == 1
        # The failing object should still be present
        assert IterDeleteFailModel.objects.count() == 1

    def test_on_error_skip_handler(self):
        IterDeleteFailModel.objects.bulk_create(
            [
                IterDeleteFailModel(name="ok-1"),
                IterDeleteFailModel(name="bad-1"),
                IterDeleteFailModel(name="ok-2"),
            ]
        )

        def handler(exc, obj):
            return IterativeDeleteErrorAction.SKIP

        count, details = IterDeleteFailModel.objects.all().iterative_delete(
            on_error=handler
        )
        assert count == 2
        assert "__errors__" not in details
        assert IterDeleteFailModel.objects.count() == 1

    def test_default_raises_without_collect_or_handler(self):
        IterDeleteFailModel.objects.bulk_create(
            [
                IterDeleteFailModel(name="ok-1"),
                IterDeleteFailModel(name="bad-1"),
                IterDeleteFailModel(name="ok-2"),
            ]
        )
        with self.assertRaises(ValueError):
            IterDeleteFailModel.objects.all().iterative_delete()
