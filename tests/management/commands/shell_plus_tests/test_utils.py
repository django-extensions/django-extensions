# -*- coding: utf-8 -*-
import sys
from io import StringIO
from typing import Dict, Set, Type  # noqa

from django.test import TestCase
from django_extensions.management.commands import shell_plus


class AutomaticShellPlusImportsTestCase(TestCase):
    def setUp(self):
        super().setUp()
        sys.stdout = StringIO()
        sys.stderr = StringIO()
        self.imported_objects = {}  # type: Dict[str, Type]
        self.output = ""

    def get_all_names_for_class(self, model_to_find_occurrences):  # type: (Type) -> Set[str]
        """
        Returns all names under current class is imported.
        :param model_to_find_occurrences: class to find names
        :return: set of names under class is imported.
        """
        result = set()
        for name, model_class in self.imported_objects.items():
            if model_class == model_to_find_occurrences:
                result.add(name)
        return result

    def assert_imported_under_names(self, model_class, names_under_model_is_available):  # type: (Type, Set[str]) -> ()
        """
        Function which asserts that class is available under given names and not available under any other name.
        :param model_class: class to assert availability.
        :param names_under_model_is_available: names under which class should be available.
        """
        self.assertSetEqual(self.get_all_names_for_class(model_class), names_under_model_is_available)
        imports_output = self.output.split("from ")
        for line in imports_output:
            if line.startswith(model_class.__module__):
                for name in names_under_model_is_available:
                    # assert that in print imports this model occurs only under names from parameter
                    if name == model_class.__name__:
                        expected_output = name
                    else:
                        expected_output = "%s (as %s)" % (model_class.__name__, name)
                    line = line.replace(expected_output, '', 1)
                self.assertNotIn(line, model_class.__name__)

    def run_shell_plus(self):
        command = shell_plus.Command()
        self.imported_objects = command.get_imported_objects({})
        self.output = sys.stdout.getvalue()
