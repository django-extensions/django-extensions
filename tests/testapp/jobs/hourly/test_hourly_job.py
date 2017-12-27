import mock

from django_extensions.management.jobs import HourlyJob


HOURLY_JOB_MOCK = mock.MagicMock()


class Job(HourlyJob):
    help = "My sample hourly job."

    def execute(self):
        HOURLY_JOB_MOCK()
