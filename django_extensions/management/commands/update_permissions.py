from django.core.management.base import BaseCommand
from django.contrib.auth.management import create_permissions as _create_permissions

try:
    from django.apps import apps as django_apps
    get_models = lambda: None
    get_app = django_apps.get_app_config
    get_all_apps = django_apps.get_app_configs

    def create_permissions(app, models, verbosity):
        _create_permissions(app, verbosity)

except ImportError:
    from django.db.models import get_models, get_app
    django_apps = None

    def get_all_apps():
        apps = set()
        for model in get_models():
            apps.add(get_app(model._meta.app_label))
        return apps
    create_permissions = _create_permissions


class Command(BaseCommand):
    args = '<app app ...>'
    help = 'reloads permissions for specified apps, or all apps if no args are specified'

    def handle(self, *args, **options):
        apps = set()
        if not args:
            apps = get_all_apps()
        else:
            for arg in args:
                apps.add(get_app(arg))

        for app in apps:
            create_permissions(app, get_models(), int(options.get('verbosity', 3)))
