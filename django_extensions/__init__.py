# -*- coding: utf-8 -*-
VERSION = (3, 0, 6)


def get_version(version):
    """Dynamically calculate the version based on VERSION tuple."""
    if len(version) > 2 and version[2] is not None:
        if isinstance(version[2], int):
            str_version = "%s.%s.%s" % version[:3]
        else:
            str_version = "%s.%s_%s" % version[:3]
    else:
        str_version = "%s.%s" % version[:2]

    return str_version


__version__ = get_version(VERSION)

default_app_config = 'django_extensions.apps.DjangoExtensionsConfig'
