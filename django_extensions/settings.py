# -*- coding: utf-8 -*-
import os

from django.conf import settings

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
REPLACEMENTS = getattr(settings, 'EXTENSIONS_REPLACEMENTS', {})
