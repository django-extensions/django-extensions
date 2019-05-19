# -*- coding: utf-8 -*-
from django_extensions.management.jobs import YearlyJob

try:
    from unittest import mock
except ImportError:
    import mock


YEARLY_JOB_MOCK = mock.MagicMock()


class Job(YearlyJob):
    help = "My sample yearly job."

    def execute(self):
        YEARLY_JOB_MOCK()
