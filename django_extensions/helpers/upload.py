#!/usr/bin/env python
#-*- coding:utf-8 -*-

from datetime import datetime
import os

from django.template.defaultfilters import slugify


def slugify_filename(filename):
    name, ext = os.path.splitext(filename)
    return slugify(name) + ext


class UploadTo(object):
    def __init__(self, base="portal", strftime="%Y/%m", instance_field="title",
        max_length=None):
        self.base = base
        self.strftime = strftime
        self.instance_field = instance_field
        self.max_length = max_length

    def __call__(self, instance, filename):
        Model = type(instance)
        max_length = self.max_length
        for field in Model._meta.fields:
            if field.name == self.instance_field:
                max_length = field.max_length
        name, ext = os.path.splitext(os.path.basename(filename))
        if callable(self.instance_field):
            value = self.instance_field(instance)
        else:
            value = getattr(instance, self.instance_field)

        filename = slugify_filename("%s%s" % (value[:max_length], ext))
        return os.path.join(
            self.base, datetime.now().strftime(self.strftime), filename)
