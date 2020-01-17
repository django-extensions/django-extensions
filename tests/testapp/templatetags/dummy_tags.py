# -*- coding: utf-8 -*-
from django import template

register = template.Library()


@register.simple_tag
def dummy_tag():
    return "dummy_tag"
