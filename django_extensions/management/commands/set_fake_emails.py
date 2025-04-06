# -*- coding: utf-8 -*-
"""
set_fake_emails.py

    Give all users a new email account. Useful for testing in a
    development environment. As such, this command is only available when
    setting.DEBUG is True.

"""

from typing import List

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from django_extensions.management.utils import signalcommand

DEFAULT_FAKE_EMAIL = "%(username)s@example.com"


class Command(BaseCommand):
    help = (
        "DEBUG only: give all users a new email based on their account data "
        '("%s" by default). '
        "Possible parameters are: username, first_name, last_name"
    ) % (DEFAULT_FAKE_EMAIL,)
    requires_system_checks: List[str] = []

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument(
            "--email",
            dest="default_email",
            default=DEFAULT_FAKE_EMAIL,
            help="Use this as the new email format.",
        )
        parser.add_argument(
            "-a",
            "--no-admin",
            action="store_true",
            dest="no_admin",
            default=False,
            help="Do not change administrator accounts",
        )
        parser.add_argument(
            "-s",
            "--no-staff",
            action="store_true",
            dest="no_staff",
            default=False,
            help="Do not change staff accounts",
        )
        parser.add_argument(
            "--include",
            dest="include_regexp",
            default=None,
            help="Include usernames matching this regexp.",
        )
        parser.add_argument(
            "--exclude",
            dest="exclude_regexp",
            default=None,
            help="Exclude usernames matching this regexp.",
        )
        parser.add_argument(
            "--include-groups",
            dest="include_groups",
            default=None,
            help=(
                "Include users matching this group. "
                "(use comma separation for multiple groups)"
            ),
        )
        parser.add_argument(
            "--exclude-groups",
            dest="exclude_groups",
            default=None,
            help=(
                "Exclude users matching this group. "
                "(use comma separation for multiple groups)"
            ),
        )

    @signalcommand
    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Only available in debug mode")

        from django.contrib.auth.models import Group

        email = options["default_email"]
        include_regexp = options["include_regexp"]
        exclude_regexp = options["exclude_regexp"]
        include_groups = options["include_groups"]
        exclude_groups = options["exclude_groups"]
        no_admin = options["no_admin"]
        no_staff = options["no_staff"]

        User = get_user_model()
        users = User.objects.all()
        if no_admin:
            users = users.exclude(is_superuser=True)
        if no_staff:
            users = users.exclude(is_staff=True)
        if exclude_groups:
            groups = Group.objects.filter(name__in=exclude_groups.split(","))
            if groups:
                users = users.exclude(groups__in=groups)
            else:
                raise CommandError("No groups matches filter: %s" % exclude_groups)
        if include_groups:
            groups = Group.objects.filter(name__in=include_groups.split(","))
            if groups:
                users = users.filter(groups__in=groups)
            else:
                raise CommandError("No groups matches filter: %s" % include_groups)
        if exclude_regexp:
            users = users.exclude(username__regex=exclude_regexp)
        if include_regexp:
            users = users.filter(username__regex=include_regexp)
        for user in users:
            user.email = email % {
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            }
            user.save()
        print("Changed %d emails" % users.count())
