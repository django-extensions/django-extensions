from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = "Print the active Django settings."

    def handle(self, *args, **options):
        for key in dir(settings):
            if key.startswith('__'):
                continue

            value = getattr(settings, key)
            print('%-40s : %s' % (key, value))
