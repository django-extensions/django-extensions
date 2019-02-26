# -*- coding: utf-8 -*-
import logging
import os
import sys

from django_extensions.management.signals import post_command, pre_command


def _make_writeable(filename):
    """
    Make sure that the file is writeable. Useful if our source is
    read-only.
    """
    import stat
    if sys.platform.startswith('java'):
        # On Jython there is no os.access()
        return
    if not os.access(filename, os.W_OK):
        st = os.stat(filename)
        new_permissions = stat.S_IMODE(st.st_mode) | stat.S_IWUSR
        os.chmod(filename, new_permissions)


def setup_logger(logger, stream, filename=None, fmt=None):
    """
    Set up a logger (if no handlers exist) for console output,
    and file 'tee' output if desired.
    """
    if len(logger.handlers) < 1:
        console = logging.StreamHandler(stream)
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter(fmt))
        logger.addHandler(console)
        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        if filename:
            outfile = logging.FileHandler(filename)
            outfile.setLevel(logging.INFO)
            outfile.setFormatter(logging.Formatter("%(asctime)s " + (fmt if fmt else '%(message)s')))
            logger.addHandler(outfile)


class RedirectHandler(logging.Handler):
    """Redirect logging sent to one logger (name) to another."""

    def __init__(self, name, level=logging.DEBUG):
        # Contemplate feasibility of copying a destination (allow original handler) and redirecting.
        logging.Handler.__init__(self, level)
        self.name = name
        self.logger = logging.getLogger(name)

    def emit(self, record):
        self.logger.handle(record)


def signalcommand(func):
    """Python decorator for management command handle defs that sends out a pre/post signal."""

    def inner(self, *args, **kwargs):
        pre_command.send(self.__class__, args=args, kwargs=kwargs)
        ret = func(self, *args, **kwargs)
        post_command.send(self.__class__, args=args, kwargs=kwargs, outcome=ret)
        return ret
    return inner


def has_ipdb():
    try:
        import ipdb  # noqa
        import IPython  # noqa
        return True
    except ImportError:
        return False
