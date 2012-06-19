import os
from optparse import make_option
from django.core.management.base import BaseCommand
from django.core.management.color import color_style
from django.template import Template

#
# TODO: Render the template with fake request object ?
#

class Command(BaseCommand):
    args = ''
    help = "Check template on syntax and compile errors"
    option_list = BaseCommand.option_list + (
        make_option('--break', '-b', action='store_true', dest='break',
                    default=False, help="Break on first error."),
        make_option('--include', '-i', action='append', dest='includes',
                    default=[], help="Append these paths to TEMPLATE_DIRS")
    )

    def handle(self, *args, **options):
        style = color_style()
        from django.conf import settings
        template_dirs = set(settings.TEMPLATE_DIRS)
        template_dirs |= set(options.get('includes', []))
        template_dirs |= set(getattr(settings, 'CHECK_TEMPLATES_EXTRA_TEMPLATE_DIRS', []))
        settings.TEMPLATE_DIRS = list(template_dirs)
        verbosity = int(options.get('verbosity', 1))
        for template_dir in template_dirs:
            for root, dirs, filenames in os.walk(template_dir):
                for filename in filenames:
                    if filename.endswith(".swp"):
                        continue
                    filepath = os.path.join(root, filename)
                    if verbosity>1:
                        print filepath
                    try:
                        tmpl = Template(open(filepath).read())
                    except Exception, e:
                        print "%s:" % filepath
                        print style.ERROR(str(e))
                        print
                        if options.get('break', False):
                            return
