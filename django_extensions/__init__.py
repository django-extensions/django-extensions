# -*- coding: utf-8 -*-
VERSION = (3, 1, 3, 'dev')


def get_version(version):
    """Dynamically calculate the version based on VERSION tuple."""
    if len(version) > 2 and version[2] is not None:
        if len(version) == 4:
            str_version = "%s.%s.%s.%s" % version
        elif isinstance(version[2], int):
            str_version = "%s.%s.%s" % version[:3]
        else:
            str_version = "%s.%s_%s" % version[:3]
    else:
        str_version = "%s.%s" % version[:2]

    return str_version


__version__ = get_version(VERSION)

try:
    import django

    if django.VERSION < (3, 2):
        default_app_config = 'django_extensions.apps.DjangoExtensionsConfig'
except ModuleNotFoundError:
    # this part is useful for allow setup.py to be used for version checks
    pass
