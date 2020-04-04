Model extensions
================

:synopsis: Current Model Extensions

Introduction
------------

Django Extensions provides you a set of Abstract Base Classes for models
that implements commonly used patterns like holding the model's creation
and last modification dates.

Current Database Model Extensions
---------------------------------

* *ActivatorModel* - Abstract Base Class that provides a ``status``,
  ``activate_date``, and ``deactivate_date`` fields.

The ``status`` field is an ``IntegerField`` whose value is choosen from a tuple
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
and modification, respectively.

The ``TimeStampedModel`` defines following ```Meta`` options:
1. ``get_latest_by`` on ``modified`` field.
2. ``ordering`` based on ``-created`` and ``-modified`` fields.


* *IndexedTimeStampedModel* - An Abstract Base Class model that provides self-managed
  ``created`` and ``modified`` fields.

The ``IndexedTimeStampedModel`` defines following ```Meta`` options:
1. Separate ``indexes`` on ``-created``, ``-modified`` fields and a composite
   index on ``-created`` and ``-modified``.

Usage:

::
  class Cheese(TimeStampedModel):
      name = models.CharField(max_length=50, null=True, blank=True)

To override the ``Meta`` class in the concrete class with new options, then
``Meta`` of the concrete class should inherit from ``TimeStampedModel.Meta``.

::
  class Sale(TimeStampedModel):
      quantity = models.IntegerField()

      class Meta(TimeStampedModel.Meta):
          db_table = "sale"

To override the ``Meta`` options defined by ``TimeStampedModel`` in concrete
class:

::
  class Sale(TimeStampedModel):
      quantity = models.IntegerField()
      bill_id = models.IntergetField()

      class Meta(TimeStampedModel.Meta):
          db_table = "sale"
          ordering = TimeStampedModel.Meta.ordering + ("-bill_id", "quantity")

  class Sale(IndexedTimeStampedModel):
      quantity = models.IntegerField()
      bill_id = models.IntergetField()

      class Meta(TimeStampedModel.Meta):
          db_table = "sale"
          indexes = TimeStampedModel.Meta.indexes + [models.Index(fields=["quantity"])]

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
