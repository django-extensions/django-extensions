# coding=utf-8
"""
Sets up the terminal color scheme.
"""

from django.core.management import color
from django.utils import termcolors


def _dummy_style_func(msg):
    return msg


def color_style():
    style = color.color_style()
    if color.supports_color():
        style.INFO = termcolors.make_style(fg='green')
        style.WARN = termcolors.make_style(fg='yellow')
        style.BOLD = termcolors.make_style(opts=('bold',))
        style.URL = termcolors.make_style(fg='green', opts=('bold',))
        style.MODULE = termcolors.make_style(fg='yellow')
        style.MODULE_NAME = termcolors.make_style(opts=('bold',))
        style.URL_NAME = termcolors.make_style(fg='red')
    else:
        for role in ('INFO', 'WARN', 'BOLD', 'URL', 'MODULE', 'MODULE_NAME', 'URL_NAME'):
            if not hasattr(style, role):
                setattr(style, role, _dummy_style_func)
    return style
