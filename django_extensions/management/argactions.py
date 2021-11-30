# -*- coding: utf-8 -*-
import argparse

from django import forms


class StoreDateAction(argparse.Action):
    """
    Date value for action of ``argparse``.

    Usage::

        >>> parser = argparse.ArgumentParser()
        >>> parser.add_argument('--date', action=StoreDateAction, help="the date. default=%(default)s")

    """

    def __call__(self, parser, namespace, values, option_string=None):
        if values:
            df = forms.DateField()
            value = df.to_python(values)
        else:
            value = None
        setattr(namespace, self.dest, value)


class StoreTimeAction(argparse.Action):
    """
    Time value for action of ``argparse``.

    Usage::

        >>> parser = argparse.ArgumentParser()
        >>> parser.add_argument('--time', action=StoreTimeAction, help="the time. default=%(default)s")

    """

    def __call__(self, parser, namespace, values, option_string=None):
        if values:
            tf = forms.TimeField()
            value = tf.to_python(values)
        else:
            value = None

        setattr(namespace, self.dest, value)
