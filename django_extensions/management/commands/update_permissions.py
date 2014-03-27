from django.core.management.base import BaseCommand
from django.db.models import get_models, get_app
from django.contrib.auth.management import create_permissions
from django_extensions.management.signals import pre_command, post_command

class Command(BaseCommand):
    args = '<app app ...>'
    help = 'reloads permissions for specified apps, or all apps if no args are specified'

    def handle(self, *args, **options):
        pre_command.send(self.__class__)
        
        if not args:
            apps = []
            for model in get_models():
                apps.append(get_app(model._meta.app_label))
        else:
            apps = []
            for arg in args:
                apps.append(get_app(arg))
        for app in apps:
            create_permissions(app, get_models(), int(options.get('verbosity', 0)))

        post_command.send(self.__class__)