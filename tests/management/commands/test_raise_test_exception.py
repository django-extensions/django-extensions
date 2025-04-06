# -*- coding: utf-8 -*-
import pytest

from django.core.management import call_command

from django_extensions.management.commands.raise_test_exception import (
    DjangoExtensionsTestException,
)


def test_raise_test_exception():
    with pytest.raises(DjangoExtensionsTestException):
        call_command("raise_test_exception")
