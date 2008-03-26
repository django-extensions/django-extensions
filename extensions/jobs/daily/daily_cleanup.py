"""
Daily cleanup job.

Can be run as a cronjob to clean out old data from the database (only expired
sessions at the moment).
"""

from extensions.management.jobs import DailyJob

class Job(DailyJob):
    help = "Django Daily Cleanup Job"

    def execute(self):
	from django.bin.daily_cleanup import clean_up
	clean_up()