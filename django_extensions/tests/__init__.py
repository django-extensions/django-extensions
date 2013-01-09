from django.db import models  # NOQA
from django_extensions.tests.test_dumpscript import DumpScriptTests
from django_extensions.tests.utils import UTILS_TRUNCATE_LETTERS_TESTS
from django_extensions.tests.utils import UTILS_UUID_TESTS
from django_extensions.tests.json_field import JsonFieldTest
from django_extensions.tests.uuid_field import UUIDFieldTest
from django_extensions.tests.fields import AutoSlugFieldTest
from django_extensions.tests.management_command import CommandTest, ShowTemplateTagsTests

__test__ = {
    'UTILS_TRUNCATE_LETTERS_TESTS': UTILS_TRUNCATE_LETTERS_TESTS,
    'UTILS_UUID_TESTS': UTILS_UUID_TESTS,
}

__test_classes__ = [
    DumpScriptTests, JsonFieldTest, UUIDFieldTest, AutoSlugFieldTest, CommandTest, ShowTemplateTagsTests
]

try:
    from django_extensions.tests.encrypted_fields import EncryptedFieldsTestCase
    from django_extensions.tests.models import Secret  # NOQA
    __test_classes__.append(EncryptedFieldsTestCase)
except ImportError:
    pass

