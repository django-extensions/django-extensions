# -*- coding: utf-8 -*-
import base64
import os
import warnings

import django
from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

try:
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import padding
    from cryptography.hazmat.primitives.ciphers import algorithms, modes
    from cryptography.hazmat.primitives.ciphers.base import Cipher
except ImportError:
    raise ImportError('Using an encrypted field requires the cryptography module. '
                      'You can obtain cryptography from https://cryptography.io/.')


class EncryptionWarning(RuntimeWarning):
    pass


class BaseEncryptedField(models.Field):
    prefix = 'enc_str:::'

    def __init__(self, *args, **kwargs):
        if not getattr(settings, 'CRYPTOGRAPHY_ENCRYPT_ALGORITHM', None):
            raise ImproperlyConfigured('You must set the settings.CRYPTOGRAPHY_ENCRYPT_ALGORITHM '
                                       'setting to your cryptography keys directory.')

        if not getattr(settings, 'CRYPTOGRAPHY_ENCRYPT_KEY', None):
            raise ImproperlyConfigured('You must set the settings.CRYPTOGRAPHY_ENCRYPT_KEY '
                                       'setting to your cryptography keys directory.')

        crypt_class = self.get_crypt_class()
        self.key = getattr(settings, 'CRYPTOGRAPHY_ENCRYPT_KEY')
        self.backend = default_backend()
        self.algorithm = crypt_class(self.key)
        self.block_size = self.algorithm.block_size

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
        iv = os.urandom(self.block_size // 8)
        cipher = Cipher(self.algorithm, modes.CBC(os.urandom(self.block_size // 8)), backend=self.backend)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(self.block_size).padder()

        test_bytes = ('x' * unencrypted_length).encode()
        padded_data = padder.update(test_bytes) + padder.finalize()
        encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
        encrypted_data_with_iv = (
            self.prefix
            + base64.urlsafe_b64encode(encrypted_data).decode()
            + ''.join(chr(x) for x in bytearray(iv))
        )
        return len(encrypted_data_with_iv)

    def get_crypt_class(self):
        """Get the cryptography algorithms class to use."""
        cryptography_encrypt_algorithm = getattr(settings, 'CRYPTOGRAPHY_ENCRYPT_ALGORITHM')
        return getattr(algorithms, cryptography_encrypt_algorithm)

    def to_python(self, value):
        if value and (value.startswith(self.prefix)):
            iv = b''.join(bytes([ord(x[0])]) for x in value[-(self.block_size // 8):])
            cipher = Cipher(self.algorithm, modes.CBC(iv), backend=self.backend)
            decryptor = cipher.decryptor()
            padder = padding.PKCS7(self.block_size).unpadder()

            decrypted_text = decryptor.update(base64.urlsafe_b64decode(
                value[len(self.prefix):-self.block_size // 8])) + decryptor.finalize()
            unpadded_text = (padder.update(decrypted_text) + padder.finalize()).decode()
            retval = unpadded_text
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
        if value and not value.startswith(self.prefix):
            # Truncated encrypted content is unreadable,
            # so truncate before encryption
            max_length = self.unencrypted_length
            if max_length and len(value) > max_length:
                warnings.warn("Truncating field %s from %d to %d bytes" % (
                    self.name, len(value), max_length), EncryptionWarning
                )
                value = value[:max_length]

            iv = os.urandom(self.block_size // 8)
            cipher = Cipher(self.algorithm, modes.CBC(iv), backend=self.backend)
            encryptor = cipher.encryptor()
            padder = padding.PKCS7(self.block_size).padder()

            padded_data = padder.update(value.encode()) + padder.finalize()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            value = (
                self.prefix
                + base64.urlsafe_b64encode(encrypted_data).decode()
                + ''.join(chr(x) for x in bytearray(iv))
            )
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
