# -*- coding: utf-8 -*-
from django.db import models

from django_extensions.db.fields import UniqueFieldMixin


class UniqField(UniqueFieldMixin, models.CharField):
    def __init__(self, *args, **kwargs):
        self.boolean_attr = kwargs.pop('boolean_attr', False)
        self.non_boolean_attr = kwargs.pop('non_boolean_attr', 'non_boolean_attr')

        super().__init__(*args, **kwargs)
