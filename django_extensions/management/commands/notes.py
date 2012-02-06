from __future__ import with_statement
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import re

ANNOTATION_RE = re.compile("#[\s]*?(TODO|FIXME|HACK|XXX)[\s:]?(.+)")

class Command(BaseCommand):
    help = 'Show all annotations like TODO, FIXME, HACK or XXX in your py files.'
    args = 'tag'
    label = 'annotation tag (TODO, FIXME, HACK, XXX)'

    def handle(self, *args, **options):
        # don't add django internal code
        apps = filter(lambda app: not app.startswith('django.contrib'),
                        settings.INSTALLED_APPS)
        for app_dir in apps:
            for top, dirs, files in os.walk(app_dir):
                for f in files:
                    if os.path.splitext(f)[1] in ['.py']:
                        fpath = os.path.join(top, f)
                        annotation_lines = []
                        with open(fpath, 'r') as f:
                            i = 0
                            for line in f.readlines():
                                i += 1
                                if ANNOTATION_RE.search(line):
                                    tag, msg = ANNOTATION_RE.findall(line)[0]
                                    if len(args) == 1:
                                        search_for_tag = args[0].upper()
                                        if not search_for_tag == tag:
                                            break
                                    annotation_lines.append("[%3s] %-5s %s" % (i, tag, msg.strip()))
                            if annotation_lines:
                                print fpath+":"
                                for annotation in annotation_lines:
                                    print "  * "+annotation
                                print
