# -*- coding: utf-8 -*-
from typing import Optional, Set  # noqa

from django.conf import settings
from django.test.utils import override_settings

from tests.management.commands.shell_plus_tests.test_utils import AutomaticShellPlusImportsTestCase
from tests.test_module_in_project_dir import FourthDerivedClass
from tests.testapp.derived_classes_for_testing import SecondDerivedClass
from tests.testapp.derived_classes_for_testing.test_module import ClassWhichShouldNotBeImported, ThirdDerivedClass
from tests.testapp.classes_to_include import BaseIncludedClass, FirstDerivedClass, IncludedMixin


class ImportSubclassesTestCase(AutomaticShellPlusImportsTestCase):
    def test_imports_no_subclasses(self):
        self.assert_imports()

    @override_settings(
        SHELL_PLUS_SUBCLASSES_IMPORT=[],
    )
    def test_imports_empty_list(self):
        self.assert_imports()

    @override_settings(
        SHELL_PLUS_SUBCLASSES_IMPORT=[BaseIncludedClass],
    )
    def test_imports_one_base_class(self):
        self.assert_imports(
            first={'FirstDerivedClass'},
            second={'SecondDerivedClass'},
            fourth={'FourthDerivedClass'},
        )

    @override_settings(
        SHELL_PLUS_SUBCLASSES_IMPORT=['tests.testapp.classes_to_include.BaseIncludedClass'],
    )
    def test_imports_one_base_class_as_string(self):
        self.assert_imports(
            first={'FirstDerivedClass'},
            second={'SecondDerivedClass'},
            fourth={'FourthDerivedClass'},
        )

    @override_settings(
        SHELL_PLUS_SUBCLASSES_IMPORT=[IncludedMixin],
    )
    def test_imports_one_base_mixin(self):
        self.assert_imports(
            first={'FirstDerivedClass'},
            third={'ThirdDerivedClass'},
        )

    @override_settings(
        SHELL_PLUS_SUBCLASSES_IMPORT=[BaseIncludedClass, IncludedMixin],
    )
    def test_imports_two_base_classes(self):
        self.assert_imports(
            first={'FirstDerivedClass'},
            second={'SecondDerivedClass'},
            third={'ThirdDerivedClass'},
            fourth={'FourthDerivedClass'},
        )

    @override_settings(
        SHELL_PLUS_SUBCLASSES_IMPORT=[BaseIncludedClass, IncludedMixin],
        SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST=settings.SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST + [
            'tests.testapp',
        ]
    )
    def test_imports_two_base_classes_exclude_testapp(self):
        self.assert_imports(
            fourth={'FourthDerivedClass'},
        )

    @override_settings(
        SHELL_PLUS_SUBCLASSES_IMPORT=[BaseIncludedClass, IncludedMixin],
        SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST=settings.SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST + [
            'tests.testapp.derived_classes_for_testing',
        ]
    )
    def test_imports_two_base_classes_exclude_derived_class_for_testing(self):
        self.assert_imports(
            first={'FirstDerivedClass'},
            fourth={'FourthDerivedClass'},
        )

    @override_settings(
        SHELL_PLUS_SUBCLASSES_IMPORT=[BaseIncludedClass, IncludedMixin],
        SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST=settings.SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST + [
            'tests.testapp.derived_classes_for_testing.test_module',
        ]
    )
    def test_imports_two_base_classes_exclude_test_module(self):
        self.assert_imports(
            first={'FirstDerivedClass'},
            second={'SecondDerivedClass'},
            fourth={'FourthDerivedClass'},
        )

    @override_settings(
        SHELL_PLUS_SUBCLASSES_IMPORT=[BaseIncludedClass, IncludedMixin],
        SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST=settings.SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST + [
            'tests.test_module_in_project_dir',
        ]
    )
    def test_imports_two_base_classes_exclude_classes_in_project_dir(self):
        self.assert_imports(
            first={'FirstDerivedClass'},
            second={'SecondDerivedClass'},
            third={'ThirdDerivedClass'},
        )

    @override_settings(
        SHELL_PLUS_SUBCLASSES_IMPORT=[BaseIncludedClass, IncludedMixin],
        SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST=settings.SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST + [
            'tests.testapp.classes_to_include',
        ]
    )
    def test_imports_two_base_classes_exclude_classes_in_classes_to_include(self):
        self.assert_imports(
            second={'SecondDerivedClass'},
            third={'ThirdDerivedClass'},
            fourth={'FourthDerivedClass'},
        )

    def assert_imports(self, first=None, second=None, third=None, fourth=None):
        """
        Auxiliary assertion which checks are classes imported under names.
        :param first: set of expected names under which FirstDerivedClass should be available
        :param second: set of expected names under which SecondDerivedClass should be available
        :param third: set of expected names under which ThirdDerivedClass should be available
        :param fourth: set of expected names under which FourthDerivedClass should be available
        """
        # type: (Optional[Set[str]], Optional[Set[str]], Optional[Set[str]], Optional[Set[str]]) -> ()
        self.run_shell_plus()
        self.assert_imported_under_names(FirstDerivedClass, first or set())
        self.assert_imported_under_names(SecondDerivedClass, second or set())
        self.assert_imported_under_names(ThirdDerivedClass, third or set())
        self.assert_imported_under_names(FourthDerivedClass, fourth or set())
        self.assert_imported_under_names(ClassWhichShouldNotBeImported, set())
