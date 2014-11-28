Field Extensions
================

:synopsis: Current Field Extensions


Current Database Model Field Extensions
---------------------------------------

* *AutoSlugField* - AutoSlugfield will automatically create a unique slug
  incrementing an appended number on the slug until it is unique. Inspired by
  SmileyChris' Unique Slugify snippet.

* *CreationDateTimeField* - DateTimeField that will automatically set its date
  when the object is first saved to the database. Works in the same way as the
  auto_now_add keyword.

* *ModificationDateTimeField* - DateTimeField that will automatically set its
  date when an object is saved to the database. Works in the same way as the
  auto_now keyword.

* *UUIDField* - UUIDField for Django, supports all uuid versions that are
  natively supported by the uuid python module.

  .. deprecated:: 1.4.7
     Django 1.8 features a native UUIDField. Django-Extensions will support *UUIDField* at the very least until Django 1.7 becomes unsupported.

* *PostgreSQLUUIDField* - UUIDField for Django, uses PostgreSQL uuid type.

  .. deprecated:: 1.4.7
     Django 1.8 features a native UUIDField. Django-Extensions will support *UUIDField* at the very least until Django 1.7 becomes unsupported.

* *EncryptedCharField* - CharField which transparently encrypts its value as it goes in and out of the database.  Encryption is handled by `Keyczar <http://www.keyczar.org/>`_.  To use this field you must have Keyczar installed, have generated a primary encryption key, and have ``settings.ENCRYPTED_FIELD_KEYS_DIR`` set to the full path of your keys directory.

* *EncryptedTextField* - CharField which transparently encrypts its value as it goes in and out of the database.  Encryption is handled by `Keyczar <http://www.keyczar.org/>`_.  To use this field you must have Keyczar installed, have generated a primary encryption key, and have ``settings.ENCRYPTED_FIELD_KEYS_DIR`` set to the full path of your keys directory.

* *ShortUUIDField* - CharField which transparently generates a UUID and pass it to base57. It result in shorter 22 characters values useful e.g. for concise, unambiguous URLS. It's possible to get shorter values with length parameter: they are not Universal Unique any more but probability of collision is still low
