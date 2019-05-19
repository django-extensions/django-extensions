# -*- coding: utf-8 -*-
from django.test import TestCase

from django_extensions import get_version


class DjangoExtensionsVersionTests(TestCase):

    def test_patch_number_is_str(self):
        result = get_version((1, 2, 'pre'))

        self.assertEqual(result, '1.2_pre')

    def test_patch_number_is_int(self):
        result = get_version((1, 2, 3))

        self.assertEqual(result, '1.2.3')

    def test_no_patch_number(self):
        result = get_version((1, 2))

        self.assertEqual(result, '1.2')
