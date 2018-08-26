# -*- coding: utf-8 -*-
import mock

from django_extensions.management.jobs import YearlyJob


YEARLY_JOB_MOCK = mock.MagicMock()


class Job(YearlyJob):
    help = "My sample yearly job."

    def execute(self):
        YEARLY_JOB_MOCK()
