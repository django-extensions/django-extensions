# -*- coding: utf-8 -*-
import mock

from django_extensions.management.jobs import MonthlyJob


MONTHLY_JOB_MOCK = mock.MagicMock()


class Job(MonthlyJob):
    help = "My sample monthly job."

    def execute(self):
        MONTHLY_JOB_MOCK()
