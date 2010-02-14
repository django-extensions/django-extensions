from django.core.management.base import LabelCommand
from django.template.loader import find_template
from django.template import TemplateDoesNotExist
import sys

def get_template_path(path):
    try:
        template = find_template(path)
        return template[1].name
    except TemplateDoesNotExist:
        return None

class Command(LabelCommand):
    help = "Finds the location of the given template by resolving its path"
    args = "[template_path]"
    label = 'template path'

    def handle_label(self, template_path, **options):
        path = get_template_path(template_path)
        if path is None:
            sys.stderr.write("No template found\n")
            sys.exit(1)
        else:
            print path
