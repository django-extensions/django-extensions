# -*- coding: utf-8 -*-
import six
from django.utils.encoding import force_text
try:
    from django.utils.functional import keep_lazy
    KEEP_LAZY = True
except ImportError:
    from django.utils.functional import allow_lazy
    KEEP_LAZY = False


def truncate_letters(s, num):
    """
    truncates a string to a number of letters, similar to truncate_words
    """
    s = force_text(s)
    length = int(num)
    if len(s) > length:
        s = s[:length]
        if not s.endswith('...'):
            s += '...'
    return s


if KEEP_LAZY:
    truncate_letters = keep_lazy(six.text_type)(truncate_letters)
else:
    truncate_letters = allow_lazy(truncate_letters, six.text_type)
