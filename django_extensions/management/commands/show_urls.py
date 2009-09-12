from django.conf import settings
from django.core.exceptions import ViewDoesNotExist
from django.core.management.base import BaseCommand
try:
    # 2008-05-30 admindocs found in newforms-admin brand
    from django.contrib.admindocs.views import simplify_regex
except ImportError:
    # fall back to trunk, pre-NFA merge
    from django.contrib.admin.views.doc import simplify_regex
        
from django_extensions.management.color import color_style

def extract_views_from_urlpatterns(urlpatterns, base=''):
    """ 
    Return a list of views from a list of urlpatterns.

    Each object in the returned list is a two-tuple: (view_func, regex)
    """
    views = []
    for p in urlpatterns:
        if hasattr(p, '_get_callback'):
            try:
                views.append((p._get_callback(), base + p.regex.pattern, p.name))
            except ViewDoesNotExist:
                continue
        elif hasattr(p, '_get_url_patterns'):
            try:
                patterns = p.url_patterns
            except ImportError:
                continue
            views.extend(extract_views_from_urlpatterns(patterns, base + p.regex.pattern))
        else:
            raise TypeError, _("%s does not appear to be a urlpattern object") % p
    return views

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
            try:
                urlconf = __import__(settings_mod.ROOT_URLCONF, {}, {}, [''])
            except Exception, e:
                if options.get('traceback', None):
                    import traceback
                    traceback.print_exc()
                print style.ERROR("Error occurred while trying to load %s: %s" % (settings_mod.ROOT_URLCONF, str(e)))
                continue
            view_functions = extract_views_from_urlpatterns(urlconf.urlpatterns)
            for (func, regex, url_name) in view_functions:
                func_name = hasattr(func, '__name__') and func.__name__ or repr(func)
                views.append("%(url)s\t%(module)s.%(name)s\t%(url_name)s" % {'name': style.MODULE_NAME(func_name),
                                       'module': style.MODULE(func.__module__),
                                       'url_name': style.URL_NAME(url_name or ''),
                                       'url': style.URL(simplify_regex(regex))})
        return "\n".join([v for v in views])
