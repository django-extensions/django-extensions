from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from enum import Enum

from django_extensions.db.fields import (
    AutoSlugField,
    CreationDateTimeField,
    ModificationDateTimeField,
)


class TimeStampedModel(models.Model):
    """
    TimeStampedModel

    An abstract base class model that provides self-managed "created" and
    "modified" fields.
    """

    created = CreationDateTimeField(_("created"))
    modified = ModificationDateTimeField(_("modified"))

    def save(self, **kwargs):
        self.update_modified = kwargs.pop(
            "update_modified", getattr(self, "update_modified", True)
        )
        super().save(**kwargs)

    class Meta:
        get_latest_by = "modified"
        abstract = True


class TitleDescriptionModel(models.Model):
    """
    TitleDescriptionModel

    An abstract base class model that provides title and description fields.
    """

    title = models.CharField(_("title"), max_length=255)
    description = models.TextField(_("description"), blank=True, null=True)

    class Meta:
        abstract = True


class TitleSlugDescriptionModel(TitleDescriptionModel):
    """
    TitleSlugDescriptionModel

    An abstract base class model that provides title and description fields
    and a self-managed "slug" field that populates from the title.

    .. note ::
        If you want to use custom "slugify" function, you could
        define ``slugify_function`` which then will be used
        in :py:class:`AutoSlugField` to slugify ``populate_from`` field.

        See :py:class:`AutoSlugField` for more details.
    """

    slug = AutoSlugField(_("slug"), populate_from="title")

    class Meta:
        abstract = True


class ActivatorQuerySet(models.query.QuerySet):
    """
    ActivatorQuerySet

    Query set that returns statused results
    """

    def active(self):
        """Return active query set"""
        return self.filter(status=ActivatorModel.ACTIVE_STATUS)

    def inactive(self):
        """Return inactive query set"""
        return self.filter(status=ActivatorModel.INACTIVE_STATUS)


class ActivatorModelManager(models.Manager):
    """
    ActivatorModelManager

    Manager to return instances of ActivatorModel:
        SomeModel.objects.active() / .inactive()
    """

    def get_queryset(self):
        """Use ActivatorQuerySet for all results"""
        return ActivatorQuerySet(model=self.model, using=self._db)

    def active(self):
        """
        Return active instances of ActivatorModel:

        SomeModel.objects.active(), proxy to ActivatorQuerySet.active
        """
        return self.get_queryset().active()

    def inactive(self):
        """
        Return inactive instances of ActivatorModel:

        SomeModel.objects.inactive(), proxy to ActivatorQuerySet.inactive
        """
        return self.get_queryset().inactive()


class ActivatorModel(models.Model):
    """
    ActivatorModel

    An abstract base class model that provides activate and deactivate fields.
    """

    INACTIVE_STATUS = 0
    ACTIVE_STATUS = 1

    STATUS_CHOICES = (
        (INACTIVE_STATUS, _("Inactive")),
        (ACTIVE_STATUS, _("Active")),
    )
    status = models.IntegerField(
        _("status"), choices=STATUS_CHOICES, default=ACTIVE_STATUS
    )
    activate_date = models.DateTimeField(
        blank=True, null=True, help_text=_("keep empty for an immediate activation")
    )
    deactivate_date = models.DateTimeField(
        blank=True, null=True, help_text=_("keep empty for indefinite activation")
    )
    objects = ActivatorModelManager()

    class Meta:
        ordering = (
            "status",
            "-activate_date",
        )
        abstract = True

    def save(self, *args, **kwargs):
        if not self.activate_date:
            self.activate_date = now()
        super().save(*args, **kwargs)


class IterativeDeleteErrorAction(Enum):
    """Actions that an on_error handler can return during iterative deletes."""

    RAISE = "raise"
    SKIP = "skip"


class IterativeDeleteQuerySet(models.QuerySet):
    """
    QuerySet that provides an iterative_delete() method and makes delete()
    iterative by default, ensuring model.delete() and signals are executed
    for each instance. Pass non_iterative=True to use the bulk path.

    Caveat: Significantly slower than bulk deletion, but preferred when
    correctness (signals/cascades) is more important than speed.
    """

    def _accumulate_delete_result(self, acc, result):
        # result is a tuple: (count, details_dict)
        if not isinstance(result, tuple) or len(result) != 2:
            return acc
        total, details = acc
        cnt, dct = result
        total += int(cnt or 0)
        if isinstance(dct, dict):
            for k, v in dct.items():
                details[k] = details.get(k, 0) + int(v or 0)
        return total, details

    def iterative_delete(self, *, chunk_size=2000, collect_exceptions=False, on_error=None):
        """
        Iteratively delete each instance in the queryset by calling obj.delete().

        Parameters:
        - chunk_size: Number of rows fetched from the database per round-trip while
          streaming the queryset with QuerySet.iterator(). Using iterator() avoids
          caching the entire result set in memory; chunk_size controls the batch size
          of objects materialized at a time. This helps keep memory usage bounded on
          very large deletions and can reduce database and application pressure.
          Larger chunk sizes reduce the number of database round-trips but increase
          per-batch memory and the time the DB cursor stays busy; smaller values do
          the opposite. chunk_size does not batch the deletes: each instance is still
          deleted one-by-one by calling obj.delete(), preserving signals and cascades.
          On backends that support it (e.g. PostgreSQL), iterator() may use server-side
          cursors, in which case chunk_size also controls the fetch size from that cursor.
          The default (2000) is a conservative compromise; tune it based on your model
          size and database characteristics.
        - collect_exceptions: when True, continue on exceptions instead of aborting.
          This is useful when you want the deletion run to make best-effort progress
          even if some objects fail to delete, for example due to database integrity
          errors (e.g., foreign key protection/violations), business-rule checks in
          model.delete(), or failures raised by downstream signal handlers
          (pre_delete/post_delete). All captured exceptions are included in the
          returned details under the '__errors__' key as a list of dictionaries
          shaped like {'pk': obj.pk, 'exception': repr(exc)} so you can inspect or
          log them after the run.
        - on_error: optional callable (exc, obj) -> action controlling behavior
          when an exception occurs. Return one of:
            - IterativeDeleteErrorAction.RAISE: re-raise the exception immediately.
            - IterativeDeleteErrorAction.SKIP: swallow the exception and continue
              without counting the current object as deleted. Returning None or
              False is treated the same as SKIP for convenience.
            - (count, details_dict): treat as a replacement delete() result to
              accumulate (advanced usage).

        Returns a (count, details_dict) like Django's QuerySet.delete().

        Note:
        - chunk_size affects only how results are read; it does not change transaction
          boundaries. In autocommit mode each SQL statement is committed immediately;
          if you wrap the call in transaction.atomic(), the whole operation is in a
          single transaction regardless of chunk_size.
        """
        total = 0
        details = {}
        errors = [] if collect_exceptions else None
        for obj in self.iterator(chunk_size=chunk_size):
            try:
                res = obj.delete()
            except Exception as exc:  # pragma: no cover - covered by tests but keep generic
                action = None
                if on_error is not None:
                    try:
                        action = on_error(exc, obj)
                    except Exception:
                        # If handler itself blows up, follow default behavior
                        action = IterativeDeleteErrorAction.RAISE
                # If handler explicitly requests a re-raise, or there is no handler and
                # collect_exceptions=False, propagate the original exception. This mirrors
                # Django's default delete() behavior (fail-fast) when not opting-in to
                # error collection.
                if action is IterativeDeleteErrorAction.RAISE or (on_error is None and not collect_exceptions):
                    raise
                # Advanced: a handler may return a synthetic (count, details_dict) tuple
                # to be accumulated as if delete() succeeded for this object.
                if isinstance(action, tuple) and len(action) == 2:
                    res = action
                else:
                    # Otherwise we skip counting this object; optionally record the error
                    # when collect_exceptions=True so callers can inspect what failed.
                    if collect_exceptions:
                        errors.append({'pk': getattr(obj, 'pk', None), 'exception': repr(exc)})
                    # Skip counting for this object
                    continue
            total, details = self._accumulate_delete_result((total, details), res)
        if collect_exceptions and errors:
            details['__errors__'] = errors
        return total, details

    def delete(self, *args, non_iterative=False, **kwargs):  # type: ignore[override]
        """Delete objects in the queryset.

        By default this performs an iterative, signal-preserving deletion by
        calling obj.delete() for each instance. To opt in to Django's faster
        bulk deletion (which skips per-instance delete() and most signals),
        pass non_iterative=True.
        """
        if not non_iterative:
            chunk_size = kwargs.pop("chunk_size", 2000)
            collect_exceptions = kwargs.pop("collect_exceptions", False)
            on_error = kwargs.pop("on_error", None)
            return self.iterative_delete(
                chunk_size=chunk_size,
                collect_exceptions=collect_exceptions,
                on_error=on_error,
            )
        # Using the bulk path: strip our custom kwargs if someone passed them
        kwargs.pop("chunk_size", None)
        kwargs.pop("collect_exceptions", None)
        kwargs.pop("on_error", None)
        return super().delete(*args, **kwargs)

    async def aiterative_delete(self, *, chunk_size=2000, collect_exceptions=False, on_error=None):
        """
        Async variant of iterative_delete(), deleting each instance by calling
        obj.adelete() when available, otherwise offloading obj.delete() to a
        thread using asgiref.sync.sync_to_async.

        Parameters are the same as iterative_delete(). See that method's
        docstring for detailed semantics. Behavior on errors is likewise
        controlled by collect_exceptions and on_error.

        Returns a (count, details_dict) like Django's QuerySet.delete().
        """
        total = 0
        details = {}
        errors = [] if collect_exceptions else None
        # Prefer native async iteration if available (Django 4.1+)
        if hasattr(self, "aiterator"):
            async for obj in self.aiterator(chunk_size=chunk_size):  # type: ignore[attr-defined]
                try:
                    if hasattr(obj, "adelete"):
                        res = await obj.adelete()  # type: ignore[attr-defined]
                    else:
                        try:
                            from asgiref.sync import sync_to_async
                        except Exception:  # pragma: no cover - asgiref is a Django dep
                            res = obj.delete()
                        else:
                            res = await sync_to_async(obj.delete, thread_sensitive=True)()
                except Exception as exc:  # pragma: no cover - see sync variant tests
                    action = None
                    if on_error is not None:
                        try:
                            action = on_error(exc, obj)
                        except Exception:
                            action = IterativeDeleteErrorAction.RAISE
                    # If handler explicitly requests a re-raise, or there is no handler and
                    # collect_exceptions=False, propagate the original exception (fail-fast).
                    if action is IterativeDeleteErrorAction.RAISE or (on_error is None and not collect_exceptions):
                        raise
                    # Advanced: allow handler to supply a synthetic (count, details_dict)
                    # to accumulate as if delete() had succeeded for this object.
                    if isinstance(action, tuple) and len(action) == 2:
                        res = action
                    else:
                        # Otherwise skip this object and optionally record the error when
                        # collect_exceptions=True.
                        if collect_exceptions:
                            errors.append({'pk': getattr(obj, 'pk', None), 'exception': repr(exc)})
                        continue
                total, details = self._accumulate_delete_result((total, details), res)
        else:
            # Fallback: delegate to the synchronous implementation to avoid duplication
            return self.iterative_delete(
                chunk_size=chunk_size,
                collect_exceptions=collect_exceptions,
                on_error=on_error,
            )
        if collect_exceptions and errors:
            details['__errors__'] = errors
        return total, details


class IterativeDeleteManager(models.Manager.from_queryset(IterativeDeleteQuerySet)):  # type: ignore[misc]
    """
    Manager that enables iterative, signal-preserving deletions.

    Usage:
        class Person(models.Model):
            ...
            objects = IterativeDeleteManager()

        Person.objects.filter(...).iterative_delete()
        # or simply (iterative by default):
        Person.objects.filter(...).delete()
        # to use bulk delete (no per-instance delete/signals):
        Person.objects.filter(...).delete(non_iterative=True)

    An async variant is available as .aiterative_delete() when running under
    Django versions that support async query iteration and adelete().
    """

    pass
