from random import choice

from django.core.management.base import NoArgsCommand

from django_extensions.management.utils import signalcommand


class Command(NoArgsCommand):
    help = "Generates a new SECRET_KEY that can be used in a project settings file."

    requires_system_checks = False

    @signalcommand
    def handle_noargs(self, **options):
        return ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)') for i in range(50)])
