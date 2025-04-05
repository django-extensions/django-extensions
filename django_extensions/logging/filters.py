# -*- coding: utf-8 -*-
import time
import logging
from hashlib import md5

# also see: https://djangosnippets.org/snippets/2242/


class RateLimiterFilter(logging.Filter):
    def filter(self, record):
        from django.conf import settings
        from django.core.cache import cache

        # Rate is specified as 1 messages logged per N seconds. (aka cache timeout)
        rate = getattr(settings, "RATE_LIMITER_FILTER_RATE", 10)
        prefix = getattr(settings, "RATE_LIMITER_FILTER_PREFIX", "ratelimiterfilter")

        subject = record.getMessage()
        cache_key = "%s:%s" % (prefix, md5(subject).hexdigest())
        cache_count_key = "%s:count" % cache_key

        result = cache.get_many([cache_key, cache_count_key])
        value = result.get(cache_key)
        cntr = result.get(cache_count_key)

        if not cntr:
            cntr = 1
            cache.set(cache_count_key, cntr, rate + 60)

        if value:
            cache.incr(cache_count_key)
            return False

        record.msg = "[%sx] %s" % (cntr, record.msg)
        cache.set(cache_key, time.time(), rate)
        return True
