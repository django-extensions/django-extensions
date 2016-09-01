# -*- coding: utf-8 -*-
from __future__ import unicode_literals

try:
    from unittest import mock
except ImportError:
    import mock


force_color_support = mock.patch('django.core.management.color.supports_color', autospec=True, side_effect=lambda: True)
