"""
Daily cleanup job.

Can be run as a cronjob to clean out old data from the database (only expired
sessions at the moment).
"""

from django_extensions.management.jobs import DailyJob


class Job(DailyJob):
    help = "Django Daily Cleanup Job"

    def execute(self):
        from django.core import management
        from django import VERSION

        if VERSION[:2] < (1, 5):
            management.call_command("cleanup")
        else:
            management.call_command("clearsessions")
