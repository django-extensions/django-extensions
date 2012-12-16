from django.db import models
from django.conf import settings

try:
    from django_extensions.db.fields.encrypted import EncryptedTextField, EncryptedCharField
    if not hasattr(settings, 'ENCRYPTED_FIELD_KEYS_DIR'):
        raise ImportError
except ImportError:
    class EncryptedCharField(object):
        def __init__(self, *args, **kwargs):
            pass

    class EncryptedTextField(object):
        def __init__(self, *args, **kwargs):
            pass


class Secret(models.Model):
    name = EncryptedCharField("Name", blank=True, max_length=255)
    text = EncryptedTextField("Text", blank=True)


class Name(models.Model):
    name = models.CharField(max_length=50)

