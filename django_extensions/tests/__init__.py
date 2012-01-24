from django.db import models
from django_extensions.tests.test_dumpscript import DumpScriptTests
from django_extensions.tests.utils import UTILS_TRUNCATE_LETTERS_TESTS
from django_extensions.tests.utils import UTILS_UUID_TESTS
from django_extensions.tests.json_field import JsonFieldTest
from django_extensions.tests.uuid_field import UUIDFieldTest
try:
    from django_extensions.tests.encrypted_fields import EncryptedFieldsTestCase
    from django_extensions.tests.models import Secret
except ImportError:
    pass

__test__ = {
    'UTILS_TRUNCATE_LETTERS_TESTS': UTILS_TRUNCATE_LETTERS_TESTS,
    'UTILS_UUID_TESTS': UTILS_UUID_TESTS,
}
