# -*- coding: utf-8 -*-
import warnings

from django import template
from django.template.defaultfilters import truncatechars
from django.utils.deprecation import RemovedInNextVersionWarning

register = template.Library()


@register.filter(is_safe=True)
def truncateletters(value, arg):
    """
    Truncates a string after a certain number of letters
    Argument: Number of letters to truncate after
    """
    warnings.warn(
        "`django_extensions.templatetags.truncate_letters` is deprecated. "
        "You should use `django.template.defaultfilters.truncatechars` instead",  # noqa
        RemovedInNextVersionWarning,
        stacklevel=2,
    )
    return truncatechars(value, arg)
