# -*- coding: utf-8 -*-
import os
import sys

from django.core.management.base import AppCommand

from django_extensions.management.utils import _make_writeable, signalcommand


class Command(AppCommand):
    help = "Creates a Django template tags directory structure for the given app name in the apps's directory"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--name',
            '-n',
            action='store',
            dest='tag_library_name',
            default='appname_tags',
            help='The name to use for the template tag base name. Defaults to `appname`_tags.'
        )

    requires_system_checks = False
    # Can't import settings during this command, because they haven't
    # necessarily been created.
    can_import_settings = True

    @signalcommand
    def handle_app_config(self, app_config, **options):
        app_dir = app_config.path
        tag_library_name = options['tag_library_name']
        if tag_library_name == 'appname_tags':
            tag_library_name = '%s_tags' % os.path.basename(app_dir)
        copy_template('template_tags_template', app_dir, tag_library_name)


def copy_template(template_name, copy_to, tag_library_name):
    """Copy the specified template directory to the copy_to location"""
    import django_extensions
    import shutil

    template_dir = os.path.join(django_extensions.__path__[0], 'conf', template_name)

    # walk the template structure and copies it
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
            path_new = os.path.join(copy_to, relative_dir, f.replace('sample', tag_library_name))
            if os.path.exists(path_new):
                path_new = os.path.join(copy_to, relative_dir, f)
                if os.path.exists(path_new):
                    continue
            path_new = path_new.rstrip(".tmpl")
            fp_old = open(path_old, 'r')
            fp_new = open(path_new, 'w')
            fp_new.write(fp_old.read())
            fp_old.close()
            fp_new.close()
            try:
                shutil.copymode(path_old, path_new)
                _make_writeable(path_new)
            except OSError:
                sys.stderr.write("Notice: Couldn't set permission bits on %s. You're probably using an uncommon filesystem setup. No problem.\n" % path_new)
