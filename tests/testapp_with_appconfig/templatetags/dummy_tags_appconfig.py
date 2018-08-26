# -*- coding: utf-8 -*-
from django import template

register = template.Library()


@register.simple_tag
def dummy_tag_appconfig():
    return "dummy_tag_appconfig"
