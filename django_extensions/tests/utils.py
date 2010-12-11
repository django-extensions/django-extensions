# -*- coding: utf-8 -*-

UTILS_TRUNCATE_LETTERS_TESTS = """
>>> from django_extensions.utils.text import truncate_letters
>>> truncate_letters("hello tests", 100)
u'hello tests'
>>> truncate_letters("hello tests", 5)
u'hello...'
>>> for i in range(10,-1,-1): truncate_letters("hello tests", i),i
(u'hello test...', 10)
(u'hello tes...', 9)
(u'hello te...', 8)
(u'hello t...', 7)
(u'hello ...', 6)
(u'hello...', 5)
(u'hell...', 4)
(u'hel...', 3)
(u'he...', 2)
(u'h...', 1)
(u'...', 0)
>>> truncate_letters("峠 (とうげ tōge - mountain pass)", 10)
u'\u5ce0 (\u3068\u3046\u3052 t\u014dg...'

"""

UTILS_UUID_TESTS = """
>>> from django_extensions.utils import uuid

# make a UUID using an MD5 hash of a namespace UUID and a name
>>> uuid.uuid3(uuid.NAMESPACE_DNS, 'python.org')
UUID('6fa459ea-ee8a-3ca4-894e-db77e160355e')

# make a UUID using a SHA-1 hash of a namespace UUID and a name
>>> uuid.uuid5(uuid.NAMESPACE_DNS, 'python.org')
UUID('886313e1-3b8a-5372-9b90-0c9aee199e5d')

# make a UUID from a string of hex digits (braces and hyphens ignored)
>>> x = uuid.UUID('{00010203-0405-0607-0809-0a0b0c0d0e0f}')

# convert a UUID to a string of hex digits in standard form
>>> str(x)
'00010203-0405-0607-0809-0a0b0c0d0e0f'

# get the raw 16 bytes of the UUID
>>> x.bytes
'\\x00\\x01\\x02\\x03\\x04\\x05\\x06\\x07\\x08\\t\\n\\x0b\\x0c\\r\\x0e\\x0f'

# make a UUID from a 16-byte string
>>> uuid.UUID(bytes=x.bytes)
UUID('00010203-0405-0607-0809-0a0b0c0d0e0f')
"""
