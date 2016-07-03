# -*- coding: utf-8 -*-
import os
import sys
import shutil

from django.apps import apps
from django.core.management.base import AppCommand
from django.core.management.color import color_style

from django_extensions.management.utils import _make_writeable, signalcommand


class Command(AppCommand):
    help = ("Creates a Django management command directory structure for the given app name"
            " in the app's directory.")
    label = 'application name'

    requires_system_checks = False
    # Can't import settings during this command, because they haven't
    # necessarily been created.
    can_import_settings = True

    def add_arguments(self, parser):
        parser.add_argument('app_name')
        parser.add_argument(
            '--name', '-n', action='store', dest='command_name',
            default='sample',
            help='The name to use for the management command')

    @signalcommand
    def handle(self, *args, **options):
        app = apps.get_app_config(options['app_name'])
        copy_template('command_template', app.path, **options)


def copy_template(template_name, copy_to, **options):
    """copies the specified template directory to the copy_to location"""
    import django_extensions

    style = color_style()
    ERROR = getattr(style, 'ERROR', lambda x: x)
    SUCCESS = getattr(style, 'SUCCESS', lambda x: x)

    command_name, base_command = options.get('command_name'), '%sCommand' % options.get('base_command')

    template_dir = os.path.join(django_extensions.__path__[0], 'conf', template_name)

    # walks the template structure and copies it
    for d, subdirs, files in os.walk(template_dir):
        relative_dir = d[len(template_dir) + 1:]
        if relative_dir and not os.path.exists(os.path.join(copy_to, relative_dir)):
            os.mkdir(os.path.join(copy_to, relative_dir))
        for i, subdir in enumerate(subdirs):
            if subdir.startswith('.'):
                del subdirs[i]
        for f in files:
            if f.endswith('.pyc') or f.endswith('.pyo') or f.startswith('.DS_Store') or f.startswith('__pycache__'):
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
                    fp_new.write(fp_orig.read().replace('{{ command_name }}', command_name).replace('{{ base_command }}', base_command))
            try:
                shutil.copymode(path_old, path_new)
                _make_writeable(path_new)
            except OSError:
                sys.stderr.write("Notice: Couldn't set permission bits on %s. You're probably using an uncommon filesystem setup. No problem.\n" % path_new)
