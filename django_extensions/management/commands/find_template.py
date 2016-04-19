# coding=utf-8
import sys

from django.template import TemplateDoesNotExist, loader

from django_extensions.management.utils import signalcommand
from django_extensions.compat import CompatibilityLabelCommand as LabelCommand


def get_template_path(path):
    try:
        template = loader.get_template(path)
        return template.origin.name
    except TemplateDoesNotExist:
        return None


class Command(LabelCommand):
    help = "Finds the location of the given template by resolving its path"
    args = "[template_path]"
    label = 'template path'

    @signalcommand
    def handle_label(self, template_path, **options):
        path = get_template_path(template_path)
        if path is None:
            sys.stderr.write("No template found\n")
            sys.exit(1)
        else:
            print(path)
