from django.conf import settings
from django.core.management.base import BaseCommand
from django.contrib.admindocs.views import extract_views_from_urlpatterns, simplify_regex
from extensions.management.commands.color import color_style

class Command(BaseCommand):
    help = "Displays all of the url matching routes for the project."
    
    requires_model_validation = True
    
    def handle(self, *args, **options):
        if args:
            appname, = args
        
        style = color_style()
        
    	if settings.ADMIN_FOR:
            settings_modules = [__import__(m, {}, {}, ['']) for m in settings.ADMIN_FOR]
        else:
            settings_modules = [settings]
        
        views = []
        for settings_mod in settings_modules:
            urlconf = __import__(settings_mod.ROOT_URLCONF, {}, {}, [''])
            view_functions = extract_views_from_urlpatterns(urlconf.urlpatterns)
            for (func, regex) in view_functions:
                views.append("%(url)s\t%(module)s.%(name)s" % {'name': style.MODULE_NAME(func.__name__),
                                       'module': style.MODULE(func.__module__),
                                       'url': style.URL(simplify_regex(regex))})
        
        return "\n".join([v for v in views])