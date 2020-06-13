# -*- coding: utf-8 -*-
import base64
import warnings

import django
from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

try:
    from cryptography.fernet import Fernet
except ImportError:
    raise ImportError('Using an encrypted field requires the cryptography module. '
                      'You can obtain cryptography from https://cryptography.io/.')


class EncryptionWarning(RuntimeWarning):
    pass


class BaseEncryptedField(models.Field):

    def __init__(self, *args, **kwargs):
        if not getattr(settings, 'DJANGO_EXTENSIONS_ENCRYPTION_FIELDS_KEY', None):
            raise ImproperlyConfigured('You must set the settings.DJANGO_EXTENSIONS_ENCRYPTION_FIELDS_KEY.')

        self.key = getattr(settings, 'DJANGO_EXTENSIONS_ENCRYPTION_FIELDS_KEY')
        self.fernet = Fernet(self.key)

        # Encrypted size is larger than unencrypted
        self.unencrypted_length = max_length = kwargs.get('max_length', None)
        if max_length:
            kwargs['max_length'] = self.calculate_crypt_max_length(max_length)

        super().__init__(*args, **kwargs)

    def calculate_crypt_max_length(self, unencrypted_length):
        # TODO: Re-examine if this logic will actually make a large-enough
        # max-length for unicode strings that have non-ascii characters in them.
        # For PostGreSQL we might as well always use textfield since there is little
        # difference (except for length checking) between varchar and text in PG.
        test_bytes = ('x' * unencrypted_length).encode()
        encrypted_data = base64.urlsafe_b64encode(self.fernet.encrypt(test_bytes)).decode()
        return len(encrypted_data)

    def to_python(self, value):
        if value:
            decrypted_text = self.fernet.decrypt(
                base64.urlsafe_b64decode(value)
            )
            retval = decrypted_text.decode()
        else:
            retval = value
        return retval

    if django.VERSION < (2, ):
        def from_db_value(self, value, expression, connection, context):
            return self.to_python(value)
    else:
        def from_db_value(self, value, expression, connection):  # type: ignore
            return self.to_python(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        # Truncated encrypted content is unreadable,
        # so truncate before encryption
        max_length = self.unencrypted_length
        if max_length and len(value) > max_length:
            warnings.warn("Truncating field %s from %d to %d bytes" % (
                self.name, len(value), max_length), EncryptionWarning
            )
            value = value[:max_length]

        encrypted_data = self.fernet.encrypt(value.encode())
        value = base64.urlsafe_b64encode(encrypted_data).decode()

        return value

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        kwargs['max_length'] = self.unencrypted_length
        return name, path, args, kwargs


class EncryptedTextField(BaseEncryptedField):
    def get_internal_type(self):
        return 'TextField'

    def formfield(self, **kwargs):
        defaults = {'widget': forms.Textarea}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class EncryptedCharField(BaseEncryptedField):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"

    def formfield(self, **kwargs):
        defaults = {'max_length': self.max_length}
        defaults.update(kwargs)
        return super().formfield(**defaults)
