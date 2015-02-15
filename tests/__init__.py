from django.db import models  # NOQA
from .test_dumpscript import DumpScriptTests
from .test_utils import TruncateLetterTests
from .test_json_field import JsonFieldTest
from .test_uuid_field import (UUIDFieldTest, PostgreSQLUUIDFieldTest)
from .test_shortuuid_field import ShortUUIDFieldTest
from .test_fields import AutoSlugFieldTest
from .test_management_command import (CommandTest, ShowTemplateTagsTests,
                                      UpdatePermissionsTests,
                                      CommandSignalTests)
from .test_templatetags import TemplateTagsTests
from .test_clean_pyc import CleanPycTests
from .test_compile_pyc import CompilePycTests

__test_classes__ = [
    DumpScriptTests, JsonFieldTest, UUIDFieldTest, AutoSlugFieldTest,
    CommandTest, ShowTemplateTagsTests, TruncateLetterTests, TemplateTagsTests,
    ShortUUIDFieldTest, PostgreSQLUUIDFieldTest, CleanPycTests, CompilePycTests,
    UpdatePermissionsTests, CommandSignalTests
]

try:
    from .encrypted_fields import EncryptedFieldsTestCase
    __test_classes__.append(EncryptedFieldsTestCase)
except ImportError:
    pass
