# -*- coding: utf-8 -*-
from unittest import mock

force_color_support = mock.patch('django.core.management.color.supports_color', autospec=True, side_effect=lambda: True)
