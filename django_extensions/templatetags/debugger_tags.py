# -*- coding: utf-8 -*-
"""
Make debugging Django templates easier.

Example:

    {% load debugger_tags %}

    {{ object|ipdb }}

"""

from django import template


register = template.Library()


@register.filter
def ipdb(obj):  # pragma: no cover
    """Interactive Python debugger filter."""
    __import__("ipdb").set_trace()
    return obj


@register.filter
def pdb(obj):
    """Python debugger filter."""
    __import__("pdb").set_trace()
    return obj


@register.filter
def wdb(obj):  # pragma: no cover
    """Web debugger filter."""
    __import__("wdb").set_trace()
    return obj
