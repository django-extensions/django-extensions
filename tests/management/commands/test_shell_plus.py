# -*- coding: utf-8 -*-
from django_extensions.management.commands import shell_plus
from django_extensions.management.shells import SHELL_PLUS_DJANGO_IMPORTS


def test_shell_plus_get_imported_objects():
    command = shell_plus.Command()
    objs = command.get_imported_objects({})
    for items in SHELL_PLUS_DJANGO_IMPORTS.values():
        for item in items:
            assert item in objs, "%s not loaded by get_imported_objects()" % item
