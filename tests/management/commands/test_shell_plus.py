# -*- coding: utf-8 -*-
import inspect

from django.db.models import Model
from django.test import override_settings

from django_extensions.management.commands import shell_plus
from django_extensions.management.shells import SHELL_PLUS_DJANGO_IMPORTS


def test_shell_plus_get_imported_objects():
    command = shell_plus.Command()
    objs = command.get_imported_objects({})
    for items in SHELL_PLUS_DJANGO_IMPORTS.values():
        for item in items:
            assert item in objs, "%s not loaded by get_imported_objects()" % item


def assert_should_models_be_imported(should_be, cli_arguments=None):
    command = shell_plus.Command()
    objs = command.get_imported_objects(cli_arguments or {})
    imported_models = filter(lambda imported: inspect.isclass(imported) and issubclass(imported, Model), objs.values())
    assert bool(list(imported_models)) == should_be


def test_shell_plus_loading_models():
    assert_should_models_be_imported(True)


def test_shell_plus_skipping_models_import_cli():
    assert_should_models_be_imported(False, cli_arguments={'dont_load': ['*']})


@override_settings(SHELL_PLUS_DONT_LOAD=['*'])
def test_shell_plus_skipping_models_import_settings():
    assert_should_models_be_imported(False)
