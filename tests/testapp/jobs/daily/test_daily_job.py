# -*- coding: utf-8 -*-
from django_extensions.management.jobs import DailyJob

from unittest import mock


DAILY_JOB_MOCK = mock.MagicMock()


class Job(DailyJob):
    help = "My sample daily job."

    def execute(self):
        DAILY_JOB_MOCK()
