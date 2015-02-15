# -*- coding: utf-8 -*-
import six

from django.test import TestCase

from django_extensions.utils.text import truncate_letters


class TruncateLetterTests(TestCase):
    def test_truncate_more_than_text_length(self):
        self.assertEqual(six.u("hello tests"), truncate_letters("hello tests", 100))

    def test_truncate_text(self):
        self.assertEqual(six.u("hello..."), truncate_letters("hello tests", 5))

    def test_truncate_with_range(self):
        for i in range(10, -1, -1):
            self.assertEqual(
                six.u('hello tests'[:i]) + '...',
                truncate_letters("hello tests", i)
            )

    def test_with_non_ascii_characters(self):
        self.assertEqual(
            six.u('\u5ce0 (\u3068\u3046\u3052 t\u014dg...'),
            truncate_letters("峠 (とうげ tōge - mountain pass)", 10)
        )
