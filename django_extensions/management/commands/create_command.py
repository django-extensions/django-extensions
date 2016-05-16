# coding=utf-8
import os
import sys
import shutil

from django.core.management.color import color_style

from django_extensions.management.utils import _make_writeable, signalcommand
from django_extensions.compat import CompatibilityAppCommand as AppCommand


class Command(AppCommand):
    help = ("Creates a Django management command directory structure for the given app name"
            " in the app's directory.")
    args = "[appname]"
    label = 'application name'

    requires_system_checks = False
    # Can't import settings during this command, because they haven't
    # necessarily been created.
    can_import_settings = True

    def add_arguments(self, parser):
        parser.add_argument(
            '--name', '-n', action='store', dest='command_name',
            default='sample',
            help='The name to use for the management command')
        parser.add_argument(
            '--base', '-b', action='store', dest='base_command',
            default='Base', help='The base class used for implementation of '
            'this command. Should be one of Base, App, Label, or NoArgs')

    @signalcommand
    def handle_app_config(self, app, **options):
        copy_template('command_template', app.path, **options)

    @signalcommand
    def handle_app(self, app, **options):
        # handle_app is RemovedInDjango19
        app_dir = os.path.dirname(app.__file__)
        copy_template('command_template', app_dir, **options)


def copy_template(template_name, copy_to, **options):
    """copies the specified template directory to the copy_to location"""
    import django_extensions

    style = color_style()
    ERROR = getattr(style, 'ERROR', lambda x: x)
    SUCCESS = getattr(style, 'SUCCESS', lambda x: x)

    command_name, base_command = options.get('command_name'), '%sCommand' % options.get('base_command')

    template_dir = os.path.join(django_extensions.__path__[0], 'conf', template_name)

    handle_method = "handle(self, *args, **options)"
    if base_command == 'AppCommand':
        handle_method = "handle_app(self, app, **options)"
    elif base_command == 'LabelCommand':
        handle_method = "handle_label(self, label, **options)"
    elif base_command == 'NoArgsCommand':
        handle_method = "handle_noargs(self, **options)"

    # walks the template structure and copies it
    for d, subdirs, files in os.walk(template_dir):
        relative_dir = d[len(template_dir) + 1:]
        if relative_dir and not os.path.exists(os.path.join(copy_to, relative_dir)):
            os.mkdir(os.path.join(copy_to, relative_dir))
        for i, subdir in enumerate(subdirs):
            if subdir.startswith('.'):
                del subdirs[i]
        for f in files:
            if f.endswith('.pyc') or f.startswith('.DS_Store'):
                continue
            path_old = os.path.join(d, f)
            path_new = os.path.join(copy_to, relative_dir, f.replace('sample', command_name)).rstrip(".tmpl")
            if os.path.exists(path_new):
                path_new = os.path.join(copy_to, relative_dir, f).rstrip(".tmpl")
                if os.path.exists(path_new):
                    if options.get('verbosity', 1) > 1:
                        print(ERROR("%s already exists" % path_new))
                    continue
            if options.get('verbosity', 1) > 1:
                print(SUCCESS("%s" % path_new))
            with open(path_old, 'r') as fp_orig:
                with open(path_new, 'w') as fp_new:
                    fp_new.write(fp_orig.read().replace('{{ command_name }}', command_name).replace('{{ base_command }}', base_command).replace('{{ handle_method }}', handle_method))
            try:
                shutil.copymode(path_old, path_new)
                _make_writeable(path_new)
            except OSError:
                sys.stderr.write("Notice: Couldn't set permission bits on %s. You're probably using an uncommon filesystem setup. No problem.\n" % path_new)
