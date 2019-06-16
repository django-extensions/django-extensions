validators
==========

:synopsis: Validator extensions

Usage
-----

Example::

    from django_extensions.validators import HexValidator

    class UserKeys(models.Model):
        user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

        public_key = models.CharField(max_length=64, validators=[HexValidator(length=64)])
        private_key = models.CharField(max_length=128, validators=[HexValidator(length=128)])


Current Database Model Field Extensions
---------------------------------------

``NoControlCharactersValidator``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Validates that Control Characters like new lines or tabs are not allowed.
Can optionally specify `whitelist` of control characters to allow.

``NoWhitespaceValidator``
~~~~~~~~~~~~~~~~~~~~~~~~~
Validates that leading and trailing whitespace is not allowed.

``HexValidator``
~~~~~~~~~~~~~~~~
Validates that the string is a valid hex string.
Can optionally also specify `length`, `min_length` and `max_length` parameters.
