# coding=utf-8
"""
JSONField automatically serializes most Python terms to JSON data.
Creates a TEXT field with a default value of "{}".  See test_json.py for
more information.

 from django.db import models
 from django_extensions.db.fields import json

 class LOL(models.Model):
     extra = json.JSONField()
"""
from __future__ import absolute_import

import json
import six
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models


def dumps(value):
    return DjangoJSONEncoder().encode(value)


def loads(txt):
    value = json.loads(
        txt,
        encoding=settings.DEFAULT_CHARSET
    )
    return value


class JSONDict(dict):
    """
    Hack so repr() called by dumpdata will output JSON instead of
    Python formatted data.  This way fixtures will work!
    """
    def __repr__(self):
        return dumps(self)


class JSONUnicode(six.text_type):
    """
    As above
    """
    def __repr__(self):
        return dumps(self)


class JSONList(list):
    """
    As above
    """
    def __repr__(self):
        return dumps(self)


class JSONField(six.with_metaclass(models.SubfieldBase, models.TextField)):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly.  Main thingy must be a dict object."""

    def __init__(self, *args, **kwargs):
        default = kwargs.get('default', None)
        if default is None:
            kwargs['default'] = '{}'
        elif isinstance(default, (list, dict)):
            kwargs['default'] = dumps(default)
        models.TextField.__init__(self, *args, **kwargs)

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""
        if value is None and not self.null:
            return {}
        elif isinstance(value, six.string_types):
            try:
                res = loads(value)
                if isinstance(res, dict):
                    return JSONDict(**res)
                elif isinstance(res, six.string_types):
                    return JSONUnicode(res)
                elif isinstance(res, list):
                    return JSONList(res)
                return res
            except ValueError:
                # value is not JSON encoded string
                return value
        else:
            return value

    def get_prep_value(self, value):
        """Do not call `to_python` method."""
        return super(models.TextField, self).get_prep_value(value)

    def get_db_prep_save(self, value, connection, **kwargs):
        """Convert our JSON object to a string before we save"""
        if value is None and self.null:
            return None
        # default values come in as strings; only non-strings should be
        # run through `dumps`
        if not isinstance(value, six.string_types):
            value = dumps(value)

        return value

    def deconstruct(self):
        name, path, args, kwargs = super(JSONField, self).deconstruct()
        if self.default == '{}':
            del kwargs['default']
        return name, path, args, kwargs
