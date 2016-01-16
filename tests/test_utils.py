# coding=utf-8
from __future__ import unicode_literals

import pytest

from django_extensions.utils.text import truncate_letters


@pytest.mark.parametrize(
    'args, expected',
    (
        (('hello tests', 100), 'hello tests'),
        (('hello tests', 5), 'hello...'),
        (('峠 (とうげ tōge - mountain pass)', 10), '\u5ce0 (\u3068\u3046\u3052 t\u014dg...'),
    )
)
def test_truncate_letter(args, expected):
    assert truncate_letters(*args) == expected
