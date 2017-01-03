# -*- coding: utf-8 -*-
# Author: AxiaCore S.A.S. http://axiacore.com
from django.core.cache import DEFAULT_CACHE_ALIAS, caches
from django.core.cache.backends.base import InvalidCacheBackendError
from django.core.management.base import BaseCommand

from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    """A simple management command which clears the site-wide cache."""
    help = 'Fully clear site-wide cache.'

    def add_arguments(self, parser):
        parser.add_argument('--cache', default=DEFAULT_CACHE_ALIAS,
                            help='Name of cache to clear')

    @signalcommand
    def handle(self, cache, *args, **kwargs):
        try:
            caches[cache].clear()
        except InvalidCacheBackendError:
            self.stderr.write('Cache "%s" is invalid!\n' % cache)
        else:
            self.stdout.write('Cache "%s" has been cleared!\n' % cache)
