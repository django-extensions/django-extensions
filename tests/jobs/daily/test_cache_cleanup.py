# -*- coding: utf-8 -*-
from django.core.cache import caches
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings


class CacheCleanupTests(TestCase):
    """Tests for cache_cleanup job."""

    def test_should_not_do_anything_if_settings_does_not_have_CACHES_settings(self):
        call_command('runjob', 'cache_cleanup', verbosity=2)

    @override_settings(CACHES={
        'test_cache': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'my_cache_table',
        }
    })
    def test_remove_all_keys_from_DatabaseCache(self):
        call_command('createcachetable')
        db_cache = caches['test_cache']
        db_cache.set('my_key', 'hello world')

        call_command('runjob', 'cache_cleanup', verbosity=2)

        self.assertIsNone(db_cache.get('my_key'))
