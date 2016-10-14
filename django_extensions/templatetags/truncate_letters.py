# -*- coding: utf-8 -*-
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter(is_safe=True)
@stringfilter
def truncateletters(value, arg):
    """
    Truncates a string after a certain number of letters

    Argument: Number of letters to truncate after
    """
    from django_extensions.utils.text import truncate_letters
    try:
        length = int(arg)
    except ValueError:  # invalid literal for int()
        return value  # Fail silently
    return truncate_letters(value, length)
