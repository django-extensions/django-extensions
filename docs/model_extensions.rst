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

The ``title`` field is ``CharField`` with a maximun length of 255 characters,
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

That field's class is a custom defined ``AutoSlugField``, based on Django's
``SlugField``. By default, it uses ``-`` as a separator, is unique and does
not accept blank values
