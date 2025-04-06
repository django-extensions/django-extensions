# -*- coding: utf-8 -*-
from django.core.management import color
from django.utils import termcolors


def _dummy_style_func(msg):
    return msg


def no_style():
    style = color.no_style()
    for role in ("INFO", "WARN", "BOLD", "URL", "MODULE", "MODULE_NAME", "URL_NAME"):
        setattr(style, role, _dummy_style_func)
    return style


def color_style():
    if color.supports_color():
        style = color.color_style()
        style.INFO = termcolors.make_style(fg="green")
        style.WARN = termcolors.make_style(fg="yellow")
        style.BOLD = termcolors.make_style(opts=("bold",))
        style.URL = termcolors.make_style(fg="green", opts=("bold",))
        style.MODULE = termcolors.make_style(fg="yellow")
        style.MODULE_NAME = termcolors.make_style(opts=("bold",))
        style.URL_NAME = termcolors.make_style(fg="red")
    else:
        style = no_style()
    return style
