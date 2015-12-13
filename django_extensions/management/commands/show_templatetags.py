import warnings

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Deprecated in favour of \"show_template_tags\". Displays template tags and filters available in the current project."

    def handle(self, *args, **options):
        warnings.warn(
            "Deprecated: "
            "\"show_templatetags\" is depreciated and will be "
            "removed in future releases. Use \"show_template_tags\" instead.",
            DeprecationWarning)
        call_command('show_template_tags', **options)
