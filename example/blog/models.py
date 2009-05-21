from django.db import models
from django.contrib.auth.models import User

class Entry(models.Model):
    author = models.ForeignKey(User)
    title = models.TextField()
    body = models.TextField()

    class Meta:
        verbose_name_plural = "entries"
