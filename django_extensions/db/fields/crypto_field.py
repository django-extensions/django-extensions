import pickle
from functools import cached_property

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, FieldDoesNotExist
from django.core.checks import Error
from django.db import models
from django.utils.encoding import force_bytes

import base64

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet

__all__ = [
    "CryptoFieldMixin",
    "CryptoTextField",
    "CryptoCharField",
    "CryptoEmailField",
    "CryptoIntegerField",
    "CryptoDateField",
    "CryptoDateTimeField",
    "CryptoBigIntegerField",
    "CryptoPositiveIntegerField",
    "CryptoPositiveSmallIntegerField",
    "CryptoSmallIntegerField",
]


def to_bytes(_obj):
    if isinstance(_obj, bytes):
        return _obj
    elif isinstance(_obj, (bytearray, memoryview)):
        return force_bytes(_obj)
    else:
        return pickle.dumps(_obj)


class CryptoFieldMixin(models.Field):
    """
    A Mixin that can be ued to convert standard django model field to encrypted binary. Fields are fully encrypted in
    data base, but automatically readable in Django. Therefore there is no need for additional description of data,
    it will be handheld automatically.

    Cryptography protocol used in mixin: Fernet (symmetric encryption) provided by Cryptography (pyca/cryptography)
    """

    def __init__(self, salt_settings_env=None, password=None, *args, **kwargs):

        if salt_settings_env and not isinstance(salt_settings_env, str):
            raise ImproperlyConfigured("'salt_settings_env' must be a string")
        self.salt_settings_env = salt_settings_env
        self.password = "Password123!!!"

        if password and not isinstance(password, (str, int)):
            raise ImproperlyConfigured("'password' must be a string or int")

        if password:
            self.password = password

        if kwargs.get("primary_key"):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} does not support primary_key=True."
            )
        if kwargs.get("unique"):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} does not support unique=True."
            )
        if kwargs.get("db_index"):
            raise ImproperlyConfigured(
                f"{self.__class__.__name__} does not support db_index=True."
            )
        kwargs["null"] = True  # should be nullable, in case data field is nullable.
        kwargs["blank"] = True

        self.salt = "Salt123!!!"

        self.get_salt()

        self._internal_type = "BinaryField"
        super().__init__(*args, **kwargs)

    def get_salt(self):
        if self.salt_settings_env:
            try:
                self.salt = getattr(settings, self.salt_settings_env)
            except AttributeError:
                raise Error(
                    f"salt_settings_env {self.salt_settings_env} is not set in settings file"
                )
        else:
            pass

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        # Only include kwarg if it's not the default (None)
        if self.salt_settings_env:
            kwargs["salt_settings_env"] = self.salt_settings_env
        if self.password:
            kwargs["password"] = self.password
        return name, path, args, kwargs

    def generate_password_key(self, password, salt):
        # password = b"password"
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=to_bytes(salt),
            iterations=100000,
        )

        key = base64.urlsafe_b64encode(kdf.derive(to_bytes(password)))
        return key

    @cached_property
    def fernet_key(self):
        key = self.generate_password_key(self.password, self.salt)
        return Fernet(key)

    def encrypt(self, message):
        b_message = to_bytes(message)
        encrypted_message = self.fernet_key.encrypt(b_message)
        return encrypted_message

    def decrypt(self, encrypted_message):
        b_message = to_bytes(encrypted_message)
        decrypted_message = self.fernet_key.decrypt(b_message)
        return decrypted_message

    def get_internal_type(self):
        return self._internal_type

    def get_db_prep_value(self, value, connection, prepared=False):
        if self.empty_strings_allowed and value == bytes():
            value = ""
        value = super().get_db_prep_value(value, connection, prepared=False)
        if value is not None:
            encrypted_value = self.encrypt(value)
            return encrypted_value
            # return connection.Database.Binary(encrypted_value)

    def from_db_value(self, value, expression, connection):
        if value is not None:
            data = self.decrypt(value)
            return pickle.loads(data)

    @cached_property
    def validators(self):
        # For IntegerField (and subclasses) we must pretend to be that
        # field type to get proper validators.
        self._internal_type = super().get_internal_type()
        try:
            return super().validators
        finally:
            self._internal_type = "BinaryField"


class CryptoTextField(CryptoFieldMixin, models.TextField):
    pass


class CryptoCharField(CryptoFieldMixin, models.CharField):
    pass


class CryptoEmailField(CryptoFieldMixin, models.EmailField):
    pass


class CryptoIntegerField(CryptoFieldMixin, models.IntegerField):
    pass


class CryptoPositiveIntegerField(CryptoFieldMixin, models.PositiveIntegerField):
    pass


class CryptoPositiveSmallIntegerField(
    CryptoFieldMixin, models.PositiveSmallIntegerField
):
    pass


class CryptoSmallIntegerField(CryptoFieldMixin, models.SmallIntegerField):
    pass


class CryptoBigIntegerField(CryptoFieldMixin, models.BigIntegerField):
    pass


class CryptoDateField(CryptoFieldMixin, models.DateField):
    pass


class CryptoDateTimeField(CryptoFieldMixin, models.DateTimeField):
    pass
