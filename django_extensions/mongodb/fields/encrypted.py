# -*- coding: utf-8 -*-
import base64

from django import forms
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from mongoengine.base import BaseField

try:
    from cryptography.fernet import Fernet
except ImportError:
    raise ImportError('Using an encrypted field requires the cryptography module. '
                      'You can obtain cryptography from https://cryptography.io/.')


class BaseEncryptedField(BaseField):

    def __init__(self, *args, **kwargs):
        if not getattr(settings, 'DJANGO_EXTENSIONS_ENCRYPTION_FIELDS_KEY', None):
            raise ImproperlyConfigured('You must set the settings.DJANGO_EXTENSIONS_ENCRYPTION_FIELDS_KEY.')

        self.key = getattr(settings, 'DJANGO_EXTENSIONS_ENCRYPTION_FIELDS_KEY')
        self.fernet = Fernet(self.key)

        super().__init__(*args, **kwargs)

    def to_python(self, value):
        retval = value
        try:
            if value:
                decrypted_text = self.fernet.decrypt(
                    base64.urlsafe_b64decode(value)
                )
                retval = decrypted_text.decode()
        except Exception:
            pass
        return retval

    def to_mongo(self, value):
        if value:
            encrypted_data = self.fernet.encrypt(value.encode())
            value = base64.urlsafe_b64encode(encrypted_data).decode()

        return value


class EncryptedTextField(BaseEncryptedField):
    def get_internal_type(self):
        return 'StringField'

    def formfield(self, **kwargs):
        defaults = {'widget': forms.Textarea}
        defaults.update(kwargs)
        return super().formfield(**defaults)


class EncryptedCharField(BaseEncryptedField):
    def get_internal_type(self):
        return "StringField"

    def formfield(self, **kwargs):
        defaults = {'max_length': self.max_length}
        defaults.update(kwargs)
        return super().formfield(**defaults)
