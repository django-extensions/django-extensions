import sys

PY3 = sys.version_info[0] == 3
OLD_PY2 = sys.version_info[:2] < (2, 7)

if PY3:  # pragma: no cover
    from io import StringIO  # NOQA
    import importlib  # NOQA

elif OLD_PY2:  # pragma: no cover
    from cStringIO import StringIO  # NOQA
    from django.utils import importlib  # NOQA

else:  # pragma: no cover
    from cStringIO import StringIO  # NOQA
    import importlib  # NOQA
