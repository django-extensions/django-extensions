# -*- coding: utf-8 -*-
import argparse
import string
import secrets
from typing import List

from django.core.management.base import BaseCommand
from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Generates a simple new password that can be used for a user password. "
    "Uses Python’s secrets module to generate passwords. Do not use this command to "
    "generate your most secure passwords."

    requires_system_checks: List[str] = []

    def add_arguments(self, parser):
        parser.add_argument(
            "-l", "--length", nargs="?", type=int, default=16, help="Password length."
        )
        parser.add_argument(
            "-c",
            "--complex",
            action=argparse.BooleanOptionalAction,
            help="More complex alphabet, includes punctuation",
        )

    @signalcommand
    def handle(self, *args, **options):
        length = options["length"]

        alphabet = string.ascii_letters + string.digits
        if options["complex"]:
            alphabet += string.punctuation
        return "".join(secrets.choice(alphabet) for i in range(length))
