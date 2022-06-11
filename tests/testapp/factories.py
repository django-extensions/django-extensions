# -*- coding: utf-8 -*-
import factory
from factory.django import DjangoModelFactory

from .models import Secret


class SecretFactory(DjangoModelFactory):
    """DjangoModelFactory for object Secret."""

    name = factory.Faker('name')
    text = factory.Faker('bs')

    class Meta:
        model = Secret
