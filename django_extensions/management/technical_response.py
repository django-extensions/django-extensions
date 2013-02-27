# flake8: noqa

import sys


def null_technical_500_response(request, exc_type, exc_value, tb):
    if sys.version_info.major < 3:
        raise exc_type, exc_value, tb
    else:
        raise exc_type(exc_value).with_traceback(tb)
