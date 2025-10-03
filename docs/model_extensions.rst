Model Extensions
================

:synopsis: Model Extensions

Introduction
------------

Django Extensions provides you a set of Abstract Base Classes for models
that implements commonly used patterns like holding the model's creation
and last modification dates.

Database Model Extensions
-------------------------

* *ActivatorModel* - Abstract Base Class that provides a ``status``,
  ``activate_date``, and ``deactivate_date`` fields.

The ``status`` field is an ``IntegerField`` whose value is chosen from a tuple
of choices - active and inactive - defaulting to active. This model also
exposes a custom manager, allowing the user to easily query for active or
inactive objects.

E.g.: ``Model.objects.active()`` returns all instances of ``Model`` that have an
active status.

* *TitleDescriptionModel* - This Abstract Base Class model provides ``title`` and ``description`` fields.

The ``title`` field is ``CharField`` with a maximum length of 255 characters,
non-nullable. ``description``. On the other hand, ``description`` is a
nullable ``TextField``.

* *TimeStampedModel* - An Abstract Base Class model that provides self-managed
  ``created`` and ``modified`` fields.

Both of the fields are customly defined in Django Extensions as
``CreationDateTimeField`` and ``ModificationDateTimeField``.
Those fields are subclasses of Django's ``DateTimeField`` and will store
the value of ``django.utils.timezone.now()`` on the model's creation
and modification, respectively

* *TitleSlugDescriptionModel* - An Abstract Base Class model that, like the
  ``TitleDescriptionModel``, provides ``title`` and ``description`` fields
  but also provides a self-managed ``slug`` field which populates from the title.

That field's class is a custom defined `AutoSlugField <field_extensions.html>`_, based on Django's
``SlugField``. By default, it uses ``-`` as a separator, is unique and does
not accept blank values.
It is possible to customize ``slugify_function``
by defining your custom function within a model:

.. code-block:: python

    # models.py

    from django.db import models

    from django_extensions.db.models import TitleSlugDescriptionModel


    class MyModel(TitleSlugDescriptionModel, models.Model):

        def slugify_function(self, content):
            """
            This function will be used to slugify
            the title (default `populate_from` field)
            """
            return content.replace('_', '-').lower()

See `AutoSlugField docs <field_extensions.html>`_ for more details.


Iterative, signal-preserving deletions
--------------------------------------

New in this branch, django-extensions provides a manager and queryset to make
queryset deletions iterative by default so that model ``delete()`` and Django's
``pre_delete``/``post_delete`` signals are executed for each instance.
This trades speed for correctness and is useful when you rely on per-instance
cleanup logic or cascading behavior that bulk deletion would skip.

Usage
~~~~~

.. code-block:: python

    from django.db import models
    from django_extensions.db.models import (
        IterativeDeleteManager,
        IterativeDeleteErrorAction,
    )

    class Person(models.Model):
        ...
        objects = IterativeDeleteManager()

    # Iterative by default (calls obj.delete() for each row)
    count, details = Person.objects.filter(is_spam=True).delete()

    # Or explicitly:
    count, details = Person.objects.filter(is_spam=True).iterative_delete(
        chunk_size=1000,
        collect_exceptions=True,
    )

    # Opt in to Django's bulk delete (skips per-instance delete and most signals)
    count, details = Person.objects.filter(is_spam=True).delete(non_iterative=True)

Error handling
~~~~~~~~~~~~~~

Both ``iterative_delete()`` and the default ``delete()`` path in the
``IterativeDeleteQuerySet`` accept:

* ``collect_exceptions`` (bool): continue when an object raises during delete
  and report problems in the returned details under the ``"__errors__"`` key.
* ``on_error`` (callable): function ``(exc, obj) -> action`` to control behavior
  when an error happens. Return one of:

  - ``IterativeDeleteErrorAction.RAISE`` to re-raise immediately (default).
  - ``IterativeDeleteErrorAction.SKIP`` to swallow and continue.
  - a synthetic ``(count, details_dict)`` to accumulate custom results.

Both methods return a standard ``(count, details_dict)`` tuple like Django's
``QuerySet.delete()``. When ``collect_exceptions=True``, details will include
an ``"__errors__"`` list of dictionaries with ``pk`` and ``exception``.

Performance and chunking
~~~~~~~~~~~~~~~~~~~~~~~~

The ``chunk_size`` parameter controls how many rows are fetched per database
round-trip when streaming the queryset with ``QuerySet.iterator()``. It does
not batch deletes: each object is still deleted one-by-one by calling
``obj.delete()``. Tune based on your database and workload. Defaults to 2000.

Async variant
~~~~~~~~~~~~~

When running on Django versions that support async iteration, an
``aiterative_delete()`` coroutine is available. It calls ``obj.adelete()`` if
present, otherwise offloads ``obj.delete()`` to a thread using
``asgiref.sync.sync_to_async``.

Caveats
~~~~~~~

* Iterative deletion is slower than bulk deletion but preserves signals.
* Transaction boundaries are unchanged by ``chunk_size``; wrap calls in
  ``transaction.atomic()`` if you need all-or-nothing semantics.
