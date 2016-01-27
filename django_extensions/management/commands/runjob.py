# coding=utf-8
from django_extensions.management.jobs import get_job, print_jobs
from django_extensions.management.utils import signalcommand
from django_extensions.compat import CompatibilityLabelCommand as LabelCommand


class Command(LabelCommand):
    help = "Run a single maintenance job."
    args = "[app_name] job_name"
    label = ""

    def add_arguments(self, parser):
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
        app_name = None
        job_name = None
        if len(args) == 1:
            job_name = args[0]
        elif len(args) == 2:
            app_name, job_name = args
        if options.get('list_jobs'):
            print_jobs(only_scheduled=False, show_when=True, show_appname=True)
        else:
            if not job_name:
                print("Run a single maintenance job. Please specify the name of the job.")
                return
            self.runjob(app_name, job_name, options)
