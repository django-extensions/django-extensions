# -*- coding: utf-8 -*-
# An app without a models.py file for issue #936
from django.db import models


class TeslaCar(models.Model):
    sentient = models.BooleanField(default=False)
