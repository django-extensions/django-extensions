# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from io import BytesIO

import csv
import six
import codecs
import importlib
import django

from django.conf import settings


#
# Django compatibility
#
def load_tag_library(libname):
    """Load a templatetag library on multiple Django versions.

    Returns None if the library isn't loaded.
    """
    if django.VERSION < (1, 9):
        from django.template.base import get_library, InvalidTemplateLibrary
        try:
            lib = get_library(libname)
            return lib
        except InvalidTemplateLibrary:
            return None
    else:
        from django.template.backends.django import get_installed_libraries
        from django.template.library import InvalidTemplateLibrary
        try:
            lib = get_installed_libraries()[libname]
            lib = importlib.import_module(lib).register
            return lib
        except (InvalidTemplateLibrary, KeyError):
            return None


def get_template_setting(template_key, default=None):
    """ Read template settings pre and post django 1.8 """
    templates_var = getattr(settings, 'TEMPLATES', None)
    if templates_var:
        for tdict in templates_var:
            if template_key in tdict:
                return tdict[template_key]
    if template_key == 'DIRS':
        pre18_template_key = 'TEMPLATES_%s' % template_key
        value = getattr(settings, pre18_template_key, default)
        return value
    return default


class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    We are using this custom UnicodeWriter for python versions 2.x
    """
    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        self.queue = BytesIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([s.encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


from csv import writer  # noqa

# Default csv.writer for PY3 versions
csv_writer = writer
if six.PY2:
    # unicode CSVWriter for PY2
    csv_writer = UnicodeWriter  # noqa
