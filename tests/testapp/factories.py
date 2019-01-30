# -*- coding: utf-8 -*-
import factory

from .models import Secret


class SecretFactory(factory.DjangoModelFactory):
    """DjangoModelFactory for object Secret."""

    name = factory.Faker('name')
    text = factory.Faker('bs')

    class Meta:
        model = Secret
