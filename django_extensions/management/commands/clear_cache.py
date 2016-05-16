# -*- coding: utf-8 -*-
# Author: AxiaCore S.A.S. http://axiacore.com
from django.core.cache import cache

from django_extensions.management.utils import signalcommand
from django_extensions.compat import CompatibilityBaseCommand as BaseCommand


class Command(BaseCommand):
    """A simple management command which clears the site-wide cache."""
    help = 'Fully clear site-wide cache.'

    @signalcommand
    def handle(self, *args, **kwargs):
        cache.clear()
        self.stdout.write('Cache has been cleared!\n')
