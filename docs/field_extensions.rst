Field Extensions
================

:synopsis: Current Field Extensions


Current Database Model Field Extensions
---------------------------------------

* *AutoSlugField* - AutoSlugfield will automatically create a unique slug
  increasing an appended number on the slug until it is unique. Inspired by
  SmileyChris' Unique Slugify snippet.

* *CreationDateTimeField* - DateTimeField that will automatically set it's date
  when the object is first saved to the database. Works in the same way as the
  deprecated auto_now_add keyword.

* *ModificationDateTimeField* - DateTimeField that will automatically set it's
  date when an object is saved to the database. Works in the same way as the
  deprecated auto_now keyword.

* *UUIDField* - UUIDField for Django, supports all uuid versions which are
  natively supported by the uuid python module.
  
* *EncryptedCharField* - CharField which transparently encrypts its value as it goes in and out of the database.  Encryption is handled by `Keyczar <http://www.keyczar.org/>`_.  To use this field you must have Keyczar installed, have generated a primary encryption key, and have ``settings.KEYS_DIR`` set to the full path of your keys directory.

* *EncryptedTextField* - CharField which transparently encrypts its value as it goes in and out of the database.  Encryption is handled by `Keyczar <http://www.keyczar.org/>`_.  To use this field you must have Keyczar installed, have generated a primary encryption key, and have ``settings.KEYS_DIR`` set to the full path of your keys directory.