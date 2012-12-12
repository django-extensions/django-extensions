
from django_extensions.management.base import LoggingBaseCommand


class Command(LoggingBaseCommand):
    help = 'Test error'

    def handle(self, *args, **options):
        print error