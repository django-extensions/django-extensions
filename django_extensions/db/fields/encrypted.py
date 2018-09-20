# -*- coding: utf-8 -*-
import warnings

import six
from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import models

try:
    from keyczar import keyczar
except ImportError:
    raise ImportError('Using an encrypted field requires the Keyczar module. '
                      'You can obtain Keyczar from http://www.keyczar.org/.')


class EncryptionWarning(RuntimeWarning):
    pass


class BaseEncryptedField(models.Field):
    prefix = 'enc_str:::'

    def __init__(self, *args, **kwargs):
        if not hasattr(settings, 'ENCRYPTED_FIELD_KEYS_DIR'):
            raise ImproperlyConfigured('You must set the settings.ENCRYPTED_FIELD_KEYS_DIR '
                                       'setting to your Keyczar keys directory.')
        crypt_class = self.get_crypt_class()
        self.crypt = crypt_class.Read(settings.ENCRYPTED_FIELD_KEYS_DIR)

        self.enforce_max_length = kwargs.pop('enforce_max_length', False)

        # Encrypted size is larger than unencrypted
        self.unencrypted_length = max_length = kwargs.get('max_length', None)
        if max_length:
            kwargs['max_length'] = self.calculate_crypt_max_length(max_length)

        super(BaseEncryptedField, self).__init__(*args, **kwargs)

    def calculate_crypt_max_length(self, unencrypted_length):
        # TODO: Re-examine if this logic will actually make a large-enough
        # max-length for unicode strings that have non-ascii characters in them.
        # For PostGreSQL we might as well always use textfield since there is little
        # difference (except for length checking) between varchar and text in PG.
        return len(self.prefix) + len(self.crypt.Encrypt('x' * unencrypted_length))

    def get_crypt_class(self):
        """
        Get the Keyczar class to use.

        The class can be customized with the ENCRYPTED_FIELD_MODE setting. By default,
        this setting is DECRYPT_AND_ENCRYPT. Set this to ENCRYPT to disable decryption.
        This is necessary if you are only providing public keys to Keyczar.

        Returns:
            keyczar.Encrypter if ENCRYPTED_FIELD_MODE is ENCRYPT.
            keyczar.Crypter if ENCRYPTED_FIELD_MODE is DECRYPT_AND_ENCRYPT.

        Override this method to customize the type of Keyczar class returned.
        """

        crypt_type = getattr(settings, 'ENCRYPTED_FIELD_MODE', 'DECRYPT_AND_ENCRYPT')
        if crypt_type == 'ENCRYPT':
            crypt_class_name = 'Encrypter'
        elif crypt_type == 'DECRYPT_AND_ENCRYPT':
            crypt_class_name = 'Crypter'
        else:
            raise ImproperlyConfigured(
                'ENCRYPTED_FIELD_MODE must be either DECRYPT_AND_ENCRYPT '
                'or ENCRYPT, not %s.' % crypt_type)
        return getattr(keyczar, crypt_class_name)

    def to_python(self, value):
        if value is None or not isinstance(value, six.text_type):
            return value

        if isinstance(self.crypt.primary_key, keyczar.keys.RsaPublicKey):
            retval = value
        elif value and (value.startswith(self.prefix)):
            if hasattr(self.crypt, 'Decrypt'):
                retval = self.crypt.Decrypt(value[len(self.prefix):])
                if six.PY2 and retval:
                    retval = retval.decode('utf-8')
            else:
                retval = value
        else:
            retval = value

        return super(BaseEncryptedField, self).to_python(retval)

    def from_db_value(self, value, expression, connection, context):
        return self.to_python(value)

    def get_db_prep_value(self, value, connection, prepared=False):
        if prepared:
            return value

        value = super(BaseEncryptedField, self).get_prep_value(value)

        if value is None or value == '' or not isinstance(value, six.text_type):
            return value

        if value and not value.startswith(self.prefix):
            # Truncated encrypted content is unreadable,
            # so truncate before encryption
            max_length = self.unencrypted_length
            if max_length and len(value) > max_length:
                #If enforcing, throw error
                if self.enforce_max_length:
                    raise ValueError(
                        'Field {0} max_length={1} encrypted_len={2}'.format(
                            self.name,
                            self.unencrypted_length,
                            len(value),
                        )
                    )

                #Otherwise warn
                warnings.warn("Truncating field %s from %d to %d bytes" % (
                    self.name, len(value), max_length), EncryptionWarning
                )
                value = value[:max_length]

            value = self.prefix + self.crypt.Encrypt(value)
        return value

    def deconstruct(self):
        name, path, args, kwargs = super(BaseEncryptedField, self).deconstruct()
        kwargs['max_length'] = self.unencrypted_length
        return name, path, args, kwargs


class EncryptedTextField(BaseEncryptedField, models.TextField):
    def get_internal_type(self):
        return 'TextField'

    def formfield(self, **kwargs):
        defaults = {'widget': forms.Textarea}
        defaults.update(kwargs)
        return super(EncryptedTextField, self).formfield(**defaults)


class EncryptedCharField(BaseEncryptedField, models.CharField):
    def __init__(self, *args, **kwargs):
        super(EncryptedCharField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "CharField"

    def formfield(self, **kwargs):
        defaults = {'max_length': self.max_length}
        defaults.update(kwargs)
        return super(EncryptedCharField, self).formfield(**defaults)


class EncryptedDateTimeField(BaseEncryptedField, models.DateTimeField):
    def __init__(self, *args, **kwargs):
        super(EncryptedDateTimeField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "DateTimeField"

    def formfield(self, **kwargs):
        defaults = {'max_length': self.max_length}
        defaults.update(kwargs)
        return super(EncryptedDateTimeField, self).formfield(**defaults)