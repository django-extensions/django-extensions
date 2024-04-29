# -*- coding: utf-8 -*-
import logging

from django.core.management.base import BaseCommand

from django_extensions.management.jobs import get_job, print_jobs
from django_extensions.management.utils import setup_logger, signalcommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run a single maintenance job."
    missing_args_message = "test"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('app_name', nargs='?')
        parser.add_argument('job_name', nargs='?')
        parser.add_argument(
            '--list', '-l', action="store_true", dest="list_jobs",
            default=False, help="List all jobs with their description"
        )
        parser.add_argument(
            '--force', '-f', action="store_true", dest="force",
            default=False, help="Run job even if it is not scheduled for this hour."
        )        

    def runjob(self, app_name, job_name, options):
        verbosity = options["verbosity"]
        force = options["force"]
        if verbosity > 1:
            logger.info("Executing job: %s (app: %s)", job_name, app_name)
        try:
            job = get_job(app_name, job_name)
        except KeyError:
            if app_name:
                logger.error("Error: Job %s for applabel %s not found", job_name, app_name)
            else:
                logger.error("Error: Job %s not found", job_name)
            logger.info("Use -l option to view all the available jobs")
            return
        try:
            j = job()
            if not j.can_run() and not force:
                logger.error("Error: Job %s (app: %s) can't run due to schedule, use --force to override.", job_name, app_name)
                return
            j._execute(force)
        except Exception:
            logger.exception("ERROR OCCURED IN JOB: %s (APP: %s)", job_name, app_name)

    @signalcommand
    def handle(self, *args, **options):
        app_name = options['app_name']
        job_name = options['job_name']

        # hack since we are using job_name nargs='?' for -l to work
        if app_name and not job_name:
            job_name = app_name
            app_name = None

        setup_logger(logger, self.stdout)

        if options['list_jobs']:
            print_jobs(only_scheduled=False, show_when=True, show_appname=True, verbose=options['verbosity'] >= 2)
        else:
            self.runjob(app_name, job_name, options)
