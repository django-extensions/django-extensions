from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django import forms
from django.conf import settings
import warnings

try:
    from keyczar import keyczar
except ImportError:
    raise ImportError('Using an encrypted field requires the Keyczar module. '
                      'You can obtain Keyczar from http://www.keyczar.org/.')

class EncryptionWarning(RuntimeWarning): pass

class BaseEncryptedField(models.Field):
    prefix = 'enc_str:::'
    def __init__(self, *args, **kwargs):
        if not hasattr(settings, 'ENCRYPTED_FIELD_KEYS_DIR'):
            raise ImproperlyConfigured('You must set the '
                'ENCRYPTED_FIELD_KEYS_DIR setting to your Keyczar keys directory.')
        self.crypt = keyczar.Crypter.Read(settings.ENCRYPTED_FIELD_KEYS_DIR)

        # Encrypted size is larger than unencrypted
        self.unencrypted_length = max_length = kwargs.get('max_length', None)
        if max_length:
            max_length = len(self.prefix) + \
                len(self.crypt.Encrypt('x'*max_length))
            # TODO: Re-examine if this logic will actually make a large-enough
            # max-length for unicode strings that have non-ascii characters in them.
            kwargs['max_length'] = max_length

        super(BaseEncryptedField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if value and (value.startswith(self.prefix)):
            retval = self.crypt.Decrypt(value[len(self.prefix):])
            if retval:
                retval = retval.decode('utf-8')
        else:
            retval = value
        return retval

    def get_db_prep_value(self, value, connection, prepared=False):
        if value and not value.startswith(self.prefix):
            # We need to encode a unicode string into a byte string, first.
            # keyczar expects a bytestring, not a unicode string.
            if type(value) == unicode:
                value = value.encode('utf-8')
            # Truncated encrypted content is unreadable,
            # so truncate before encryption
            max_length = self.unencrypted_length
            if max_length and len(value) > max_length:
                warnings.warn("Truncating field %s from %d to %d bytes" % \
                    (self.name, len(value), max_length),EncryptionWarning)
                value = value[:max_length]

            value = self.prefix + self.crypt.Encrypt(value)
        return value


class EncryptedTextField(BaseEncryptedField):
    __metaclass__ = models.SubfieldBase

    def get_internal_type(self):
        return 'TextField'

    def formfield(self, **kwargs):
        defaults = {'widget': forms.Textarea}
        defaults.update(kwargs)
        return super(EncryptedTextField, self).formfield(**defaults)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.TextField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)


class EncryptedCharField(BaseEncryptedField):
    __metaclass__ = models.SubfieldBase

    def __init__(self, max_length=None, *args, **kwargs):
        super(EncryptedCharField, self).__init__(max_length=max_length, *args, **kwargs)

    def get_internal_type(self):
        return "CharField"

    def formfield(self, **kwargs):
        defaults = {'max_length': self.max_length}
        defaults.update(kwargs)
        return super(EncryptedCharField, self).formfield(**defaults)

    def south_field_triple(self):
        "Returns a suitable description of this field for South."
        # We'll just introspect the _actual_ field.
        from south.modelsinspector import introspector
        field_class = "django.db.models.fields.CharField"
        args, kwargs = introspector(self)
        # That's our definition!
        return (field_class, args, kwargs)

