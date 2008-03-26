from django.core.management.base import LabelCommand
from optparse import make_option
from extensions.management.jobs import get_jobs, print_jobs

class Command(LabelCommand):
    option_list = LabelCommand.option_list + (
        make_option('--list', '-l', action="store_true", dest="list_jobs",
            help="List all jobs with there description"),
        make_option('--verbose', '-v', action="store_true", dest="verbose",
            help="Verbose messages"),
    )
    help = "Runs scheduled maintenance jobs."
    args = "[hourly daily weekly monthly]"
    label = ""
    
    requires_model_validation = True

    def usage_msg(self):
        print "Run scheduled jobs. Please specify 'hourly', 'daily', 'weekly' or 'monthly'"
    
    def runjobs(self, when, options):
        jobs = get_jobs(when, only_scheduled=True)
        list = jobs.keys()
        list.sort()
        for app_name, job_name in list:
            job = jobs[(app_name, job_name)]
            if options.get('verbose', False):
                print "Executing %s job: %s (app: %s)" % (when, job_name, app_name)
            try:
                job().execute()
            except Exception, e:
                import traceback
                print "ERROR OCCURED IN %s JOB: %s (APP: %s)" % (when.upper(), job_name, app_name)
                print "START TRACEBACK:"
                traceback.print_exc()
                print "END TRACEBACK\n"
    
    def runjobs_by_dispatcher(self, when, options):
        from extensions.management import signals
        from django.db import models
        from django.dispatch import dispatcher
        from django.conf import settings
    
        for app_name in settings.INSTALLED_APPS:
            try:
                __import__(app_name + '.management', '', '', [''])
            except ImportError:
                pass

        for app in models.get_apps():
            if options.get('verbose', False):
                app_name = '.'.join(app.__name__.rsplit('.')[:-1])
                print "Dispatching %s job signal for: %s" % (when, app_name)
            if when == 'hourly':
                dispatcher.send(signal=signals.run_hourly_jobs, sender=app, app=app)
            elif when == 'daily':
                dispatcher.send(signal=signals.run_daily_jobs, sender=app, app=app)
            elif when == 'weekly':
                dispatcher.send(signal=signals.run_weekly_jobs, sender=app, app=app)
            elif when == 'monthly':
                dispatcher.send(signal=signals.run_monthly_jobs, sender=app, app=app)
    
    def handle(self, *args, **options):
        when = None
        if len(args)>1:
            self.usage_msg()
            return
        elif len(args)==1:
            if not args[0] in ['hourly', 'daily', 'weekly', 'monthly']:
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
            self.runjobs_by_dispatcher(when, options)
        