# -*- coding: utf-8 -*-
from django_extensions.management.jobs import WeeklyJob

from unittest import mock


WEEKLY_JOB_MOCK = mock.MagicMock()


class Job(WeeklyJob):
    help = "My sample weekly job."

    def execute(self):
        WEEKLY_JOB_MOCK()
