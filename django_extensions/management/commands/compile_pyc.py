# -*- coding: utf-8 -*-
import fnmatch
import os
import py_compile
from os.path import join as _j
from typing import List

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Compile python bytecode files for the project."
    requires_system_checks: List[str] = []

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            "-p",
            action="store",
            dest="path",
            help="Specify path to recurse into",
        )

    @signalcommand
    def handle(self, *args, **options):
        project_root = options["path"]
        if not project_root:
            project_root = getattr(settings, "BASE_DIR", None)

        verbosity = options["verbosity"]
        if not project_root:
            raise CommandError(
                "No --path specified and settings.py does not contain BASE_DIR"
            )

        for root, dirs, filenames in os.walk(project_root):
            for filename in fnmatch.filter(filenames, "*.py"):
                full_path = _j(root, filename)
                if verbosity > 1:
                    self.stdout.write("Compiling %s...\n" % full_path)
                py_compile.compile(full_path)
