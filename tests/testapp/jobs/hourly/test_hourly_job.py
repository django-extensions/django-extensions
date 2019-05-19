# -*- coding: utf-8 -*-
from django_extensions.management.jobs import HourlyJob

try:
    from unittest import mock
except ImportError:
    import mock


HOURLY_JOB_MOCK = mock.MagicMock()


class Job(HourlyJob):
    help = "My sample hourly job."

    def execute(self):
        HOURLY_JOB_MOCK()
