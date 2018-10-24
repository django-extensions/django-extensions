# -*- coding: utf-8 -*-
from __future__ import with_statement

import os
import re
import six

from django.conf import settings
from django.core.management.base import BaseCommand

from django_extensions.compat import get_template_setting
from django_extensions.management.utils import signalcommand

ANNOTATION_RE = re.compile(r"\{?#[\s]*?(TODO|FIXME|BUG|HACK|WARNING|NOTE|XXX)[\s:]?(.+)")
ANNOTATION_END_RE = re.compile(r"(.*)#\}(.*)")


class Command(BaseCommand):
    help = 'Show all annotations like TODO, FIXME, BUG, HACK, WARNING, NOTE or XXX in your py and HTML files.'
    args = 'tag'
    label = 'annotation tag (TODO, FIXME, BUG, HACK, WARNING, NOTE, XXX)'

    @signalcommand
    def handle(self, *args, **options):
        # don't add django internal code
        apps = [app for app in filter(lambda app: not app.startswith('django.contrib'), settings.INSTALLED_APPS)]
        template_dirs = get_template_setting('DIRS', [])
        base_dir = getattr(settings, 'BASE_DIR')
        if template_dirs:
            apps += template_dirs
        for app_dir in apps:
            app_dir = app_dir.replace(".", "/")
            if base_dir:
                app_dir = os.path.join(base_dir, app_dir)
            for top, dirs, files in os.walk(app_dir):
                for fn in files:
                    if os.path.splitext(fn)[1] in ('.py', '.html'):
                        fpath = os.path.join(top, fn)
                        annotation_lines = []
                        with open(fpath, 'r') as fd:
                            i = 0
                            for line in fd.readlines():
                                i += 1
                                if ANNOTATION_RE.search(line):
                                    tag, msg = ANNOTATION_RE.findall(line)[0]
                                    if len(args) == 1:
                                        search_for_tag = args[0].upper()
                                        if not search_for_tag == tag:
                                            break

                                    if ANNOTATION_END_RE.search(msg.strip()):
                                        msg = ANNOTATION_END_RE.findall(msg.strip())[0][0]

                                    annotation_lines.append("[%3s] %-5s %s" % (i, tag, msg.strip()))
                            if annotation_lines:
                                self.stdout.write("%s:" % fpath)
                                for annotation in annotation_lines:
                                    if six.PY2:
                                        annotation = annotation.decode('utf-8')
                                    self.stdout.write("  * %s" % annotation)
                                self.stdout.write("")
