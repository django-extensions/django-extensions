# -*- coding: utf-8 -*-
from importlib import import_module
from inspect import (
    getmembers,
    isclass,
)
from pkgutil import walk_packages
from typing import (  # NOQA
    Dict,
    List,
    Tuple,
    Union,
)

from django.conf import settings
from django.utils.module_loading import import_string


class SubclassesFinder:
    def __init__(self, base_classes_from_settings):
        self.base_classes = []
        for element in base_classes_from_settings:
            if isinstance(element, str):
                element = import_string(element)
            self.base_classes.append(element)

    def _should_be_imported(self, candidate_to_import):  # type: (Tuple[str, type]) -> bool
        for base_class in self.base_classes:
            if issubclass(candidate_to_import[1], base_class):
                return True
        return False

    def collect_subclasses(self):  # type: () -> Dict[str, List[Tuple[str, str]]]
        """
        Collect all subclasses of user-defined base classes from project.
        :return: Dictionary from module name to list of tuples.
        First element of tuple is model name and second is alias.
        Currently we set alias equal to model name,
        but in future functionality of aliasing subclasses can be added.
        """
        result = {}  # type: Dict[str, List[Tuple[str, str]]]
        for loader, module_name, is_pkg in walk_packages(path=[str(settings.BASE_DIR)]):
            subclasses_from_module = self._collect_classes_from_module(module_name)
            if subclasses_from_module:
                result[module_name] = subclasses_from_module
        return result

    def _collect_classes_from_module(self, module_name):  # type: (str) -> List[Tuple[str, str]]
        for excluded_module in getattr(settings, 'SHELL_PLUS_SUBCLASSES_IMPORT_MODULES_BLACKLIST', []):
            if module_name.startswith(excluded_module):
                return []
        imported_module = import_module(module_name)
        classes_to_import = getmembers(
            imported_module, lambda element: isclass(element) and element.__module__ == imported_module.__name__
        )
        classes_to_import = list(filter(self._should_be_imported, classes_to_import))
        return [(name, name) for name, _ in classes_to_import]
