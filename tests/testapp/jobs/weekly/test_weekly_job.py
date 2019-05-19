# -*- coding: utf-8 -*-
from django_extensions.management.jobs import WeeklyJob

try:
    from unittest import mock
except ImportError:
    import mock


WEEKLY_JOB_MOCK = mock.MagicMock()


class Job(WeeklyJob):
    help = "My sample weekly job."

    def execute(self):
        WEEKLY_JOB_MOCK()
