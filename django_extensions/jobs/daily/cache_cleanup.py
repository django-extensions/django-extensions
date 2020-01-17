# -*- coding: utf-8 -*-
"""
Daily cleanup job.

Can be run as a cronjob to clean out old data from the database (only expired
sessions at the moment).
"""
import six

from django.conf import settings
from django.core.cache import caches

from django_extensions.management.jobs import DailyJob


class Job(DailyJob):
    help = "Cache (db) cleanup Job"

    def execute(self):
        if hasattr(settings, 'CACHES'):
            for cache_name, cache_options in six.iteritems(settings.CACHES):
                if cache_options['BACKEND'].endswith("DatabaseCache"):
                    cache = caches[cache_name]
                    cache.clear()
            return
