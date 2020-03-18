# -*- coding: utf-8 -*-
from django_extensions.management.jobs import MonthlyJob

try:
    from unittest import mock
except ImportError:
    import mock


MONTHLY_JOB_MOCK = mock.MagicMock()


class Job(MonthlyJob):
    help = "My sample monthly job."

    def execute(self):
        MONTHLY_JOB_MOCK()
