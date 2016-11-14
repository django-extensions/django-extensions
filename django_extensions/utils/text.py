# -*- coding: utf-8 -*-
import six
from django.utils.encoding import force_text
from django.utils.functional import allow_lazy


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


truncate_letters = allow_lazy(truncate_letters, six.text_type)
