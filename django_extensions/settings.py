# -*- coding: utf-8 -*-
import os

from django.conf import settings

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
REPLACEMENTS = {
}
add_replacements = getattr(settings, 'EXTENSIONS_REPLACEMENTS', {})
REPLACEMENTS.update(add_replacements)
