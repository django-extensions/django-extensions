from django.db import models

from django_extensions.db.fields.encrypted import EncryptedTextField, EncryptedCharField

class Secret(models.Model):
    name = EncryptedCharField(blank=True, max_length=255)
    text = EncryptedTextField(blank=True)