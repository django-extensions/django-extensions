Field Extensions
================

:synopsis: Current Field Extensions


Current Database Model Field Extensions
---------------------------------------

* *AutoSlugField* - AutoSlugfield will automatically create a unique slug
  incrementing an appended number on the slug until it is unique. Inspired by
  SmileyChris' Unique Slugify snippet.

  AutoSlugField takes a `populate_from` argument that specifies which field, list of
  fields, or model method the slug will be populated from, for instance::

    slug = AutoSlugField(populate_from=['title', 'description', 'get_author_name'])

  `populate_from` can traverse a ForeignKey relationship by using Django ORM syntax::

    slug = AutoSlugField(populate_from=['related_model__title', 'related_model__get_readable_name'])

  AutoSlugField uses Django's slugify_ function by default to "slugify" ``populate_from`` field.

  .. _slugify: https://docs.djangoproject.com/en/dev/ref/utils/#django.utils.text.slugify

  To provide custom "slugify" function you could either provide the function as
  an argument to :py:class:`~AutoSlugField` or define your ``slugify_function``
  method within a model.

1. ``slugify_function`` as an argument to :py:class:`~AutoSlugField`.

  .. code-block:: python

    # models.py

    from django.db import models

    from django_extensions.db.fields import AutoSlugField


    def my_slugify_function(content):
        return content.replace('_', '-').lower()


    class MyModel(models.Model):

        title = models.CharField(max_length=42)
        slug = AutoSlugField(populate_from='title', slugify_function=my_slugify_function)

2. ``slugify_function`` as a method within a model class.

  .. code-block:: python

    # models.py

    from django.db import models

    from django_extensions.db.fields import AutoSlugField


    class MyModel(models.Model):

        title = models.CharField(max_length=42)
        slug = AutoSlugField(populate_from='title')

        def slugify_function(self, content):
            return content.replace('_', '-').lower()

  **Important.**
  If you both provide ``slugify_function`` in a model class and
  pass ``slugify_function`` to :py:class:`~AutoSlugField` field,
  then model's ``slugify_function`` method will take precedence.

* *RandomCharField* - AutoRandomCharField will automatically create a
  unique random character field with the specified length. By default
  upper/lower case and digits are included as possible characters. Given
  a length of 8 thats yields 3.4 million possible combinations. A 12
  character field would yield about 2 billion. Below are some examples::

    >>> RandomCharField(length=8, unique=True)
    BVm9GEaE

    >>> RandomCharField(length=4, include_alpha=False)
    7097

    >>> RandomCharField(length=12, include_punctuation=True)
    k[ZS.TR,0LHO

    >>> RandomCharField(length=12, lowercase=True, include_digits=False)
    pzolbemetmok

* *CreationDateTimeField* - DateTimeField that will automatically set its date
  when the object is first saved to the database. Works in the same way as the
  auto_now_add keyword.

* *ModificationDateTimeField* - DateTimeField that will automatically set its
  date when an object is saved to the database. Works in the same way as the
  auto_now keyword. It is possible to preserve the current timestamp by setting update_modified to False::

    >>> example = MyTimeStampedModel.objects.get(pk=1)

    >>> print example.modified
    datetime.datetime(2016, 3, 18, 10, 3, 39, 740349, tzinfo=<UTC>)

    >>> example.save(update_modified=False)

    >>> print example.modified
    datetime.datetime(2016, 3, 18, 10, 3, 39, 740349, tzinfo=<UTC>)

    >>> example.save()

    >>> print example.modified
    datetime.datetime(2016, 4, 8, 14, 25, 43, 123456, tzinfo=<UTC>)

  It is also possible to set the attribute directly on the model,
  for example when you don't use the TimeStampedModel provided in this package, or when you are in a migration::

    >>> example = MyCustomModel.objects.get(pk=1)

    >>> print example.modified
    datetime.datetime(2016, 3, 18, 10, 3, 39, 740349, tzinfo=<UTC>)

    >>> example.update_modified=False

    >>> example.save()

    >>> print example.modified
    datetime.datetime(2016, 3, 18, 10, 3, 39, 740349, tzinfo=<UTC>)

* *EncryptedCharField* - CharField which transparently encrypts its value as it goes in and out of the database.  Encryption is handled by `Keyczar <http://www.keyczar.org/>`_.  To use this field you must have Keyczar installed, have generated a primary encryption key, and have ``settings.ENCRYPTED_FIELD_KEYS_DIR`` set to the full path of your keys directory.

* *EncryptedTextField* - CharField which transparently encrypts its value as it goes in and out of the database.  Encryption is handled by `Keyczar <http://www.keyczar.org/>`_.  To use this field you must have Keyczar installed, have generated a primary encryption key, and have ``settings.ENCRYPTED_FIELD_KEYS_DIR`` set to the full path of your keys directory.

* *ShortUUIDField* - CharField which transparently generates a UUID and pass it to base57. It result in shorter 22 characters values useful e.g. for concise, unambiguous URLS. It's possible to get shorter values with length parameter: they are not Universal Unique any more but probability of collision is still low

* *JSONField* - a generic TextField that neatly serializes/unserializes JSON objects seamlessly. Django 1.9 introduces a native JSONField for PostgreSQL, which is preferred for PostgreSQL users on Django 1.9 and above.
