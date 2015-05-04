import time
import logging
from hashlib import md5

# also see: https://djangosnippets.org/snippets/2242/


class RateLimiterFilter(logging.Filter):
    def filter(self, record):
        from django.conf import settings
        from django.core.cache import cache

        # Rate is specified as 1 messages logged per N seconds. (aka cache timeout)
        rate = getattr(settings, 'RATE_LIMITER_FILTER_RATE', 10)
        prefix = getattr(settings, 'RATE_LIMITER_FILTER_PREFIX', 'ratelimiterfilter')

        subject = record.getMessage()
        cache_key = "%s:%s" % (prefix, md5(subject).hexdigest())

        value = cache.get(cache_key)
        if value:
            return False

        cache.set(cache_key, time.time(), rate)
        return True
