# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand

from django_extensions.management.jobs import get_job, print_jobs
from django_extensions.management.utils import signalcommand


class Command(BaseCommand):
    help = "Run a single maintenance job."
    missing_args_message = "test"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument('app_name', nargs='?')
        parser.add_argument('job_name', nargs='?')
        parser.add_argument(
            '--list', '-l', action="store_true", dest="list_jobs",
            help="List all jobs with their description")

    def runjob(self, app_name, job_name, options):
        verbosity = int(options.get('verbosity', 1))
        if verbosity > 1:
            print("Executing job: %s (app: %s)" % (job_name, app_name))
        try:
            job = get_job(app_name, job_name)
        except KeyError:
            if app_name:
                print("Error: Job %s for applabel %s not found" % (job_name, app_name))
            else:
                print("Error: Job %s not found" % job_name)
            print("Use -l option to view all the available jobs")
            return
        try:
            job().execute()
        except Exception:
            import traceback
            print("ERROR OCCURED IN JOB: %s (APP: %s)" % (job_name, app_name))
            print("START TRACEBACK:")
            traceback.print_exc()
            print("END TRACEBACK\n")

    @signalcommand
    def handle(self, *args, **options):
        app_name = options.get('app_name')
        job_name = options.get('job_name')

        # hack since we are using job_name nargs='?' for -l to work
        if app_name and not job_name:
            job_name = app_name
            app_name = None

        if options.get('list_jobs'):
            print_jobs(only_scheduled=False, show_when=True, show_appname=True)
        else:
            if not job_name:
                print("Run a single maintenance job. Please specify the name of the job.")
                return
            self.runjob(app_name, job_name, options)
