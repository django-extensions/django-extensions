# -*- coding: utf-8 -*-
from django_extensions.management.jobs import HourlyJob

from unittest import mock


HOURLY_JOB_MOCK = mock.MagicMock()


class Job(HourlyJob):
    help = "My sample hourly job."

    def execute(self):
        HOURLY_JOB_MOCK()
