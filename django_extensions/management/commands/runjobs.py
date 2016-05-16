# coding=utf-8
from django_extensions.management.jobs import get_jobs, print_jobs
from django_extensions.management.utils import signalcommand
from django_extensions.compat import CompatibilityLabelCommand as LabelCommand


class Command(LabelCommand):
    help = "Runs scheduled maintenance jobs."
    args = "[minutely quarter_hourly hourly daily weekly monthly yearly]"
    label = ""

    def add_arguments(self, parser):
        parser.add_argument(
            '--list', '-l', action="store_true", dest="list_jobs",
            help="List all jobs with their description")

    def usage_msg(self):
        print("Run scheduled jobs. Please specify 'minutely', 'quarter_hourly', 'hourly', 'daily', 'weekly', 'monthly' or 'yearly'")

    def runjobs(self, when, options):
        verbosity = int(options.get('verbosity', 1))
        jobs = get_jobs(when, only_scheduled=True)
        for app_name, job_name in sorted(jobs.keys()):
            job = jobs[(app_name, job_name)]
            if verbosity > 1:
                print("Executing %s job: %s (app: %s)" % (when, job_name, app_name))
            try:
                job().execute()
            except Exception:
                import traceback
                print("ERROR OCCURED IN %s JOB: %s (APP: %s)" % (when.upper(), job_name, app_name))
                print("START TRACEBACK:")
                traceback.print_exc()
                print("END TRACEBACK\n")

    def runjobs_by_signals(self, when, options):
        """ Run jobs from the signals """
        # Thanks for Ian Holsman for the idea and code
        from django_extensions.compat import get_apps
        from django_extensions.management import signals
        from django.conf import settings

        verbosity = int(options.get('verbosity', 1))
        for app_name in settings.INSTALLED_APPS:
            try:
                __import__(app_name + '.management', '', '', [''])
            except ImportError:
                pass

        for app in get_apps():
            if verbosity > 1:
                app_name = '.'.join(app.__name__.rsplit('.')[:-1])
                print("Sending %s job signal for: %s" % (when, app_name))
            if when == 'minutely':
                signals.run_minutely_jobs.send(sender=app, app=app)
            elif when == 'quarter_hourly':
                signals.run_quarter_hourly_jobs.send(sender=app, app=app)
            elif when == 'hourly':
                signals.run_hourly_jobs.send(sender=app, app=app)
            elif when == 'daily':
                signals.run_daily_jobs.send(sender=app, app=app)
            elif when == 'weekly':
                signals.run_weekly_jobs.send(sender=app, app=app)
            elif when == 'monthly':
                signals.run_monthly_jobs.send(sender=app, app=app)
            elif when == 'yearly':
                signals.run_yearly_jobs.send(sender=app, app=app)

    @signalcommand
    def handle(self, *args, **options):
        when = None
        if len(args) > 1:
            self.usage_msg()
            return
        elif len(args) == 1:
            if not args[0] in ['minutely', 'quarter_hourly', 'hourly', 'daily', 'weekly', 'monthly', 'yearly']:
                self.usage_msg()
                return
            else:
                when = args[0]
        if options.get('list_jobs'):
            print_jobs(when, only_scheduled=True, show_when=True, show_appname=True)
        else:
            if not when:
                self.usage_msg()
                return
            self.runjobs(when, options)
            self.runjobs_by_signals(when, options)
