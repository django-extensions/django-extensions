from django.db import models

try:
    from django_extensions.db.fields.encrypted import EncryptedTextField, EncryptedCharField
except ImportError:
    class EncryptedCharField(object):
        def __init__(self, **kwargs):
            pass

    class EncryptedTextField(object):
        def __init__(self, **kwargs):
            pass


class Secret(models.Model):
    name = EncryptedCharField(blank=True, max_length=255)
    text = EncryptedTextField(blank=True)

class Name(models.Model):
     name = models.CharField(max_length=50)

