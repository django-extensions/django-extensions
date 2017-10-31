# -*- coding: utf-8 -*-
import sys

import six
from django.contrib.auth.models import Group, Permission
from django.test import TestCase, override_settings

from django_extensions.collision_resolvers import AppNameCR, AppsOrderCR, BaseCR, PathBasedCR
from django_extensions.management.commands import shell_plus
from tests.collisions.models import (
    Group as Group_Col,
    Name as Name_Col,
    Note as Note_Col,
    SystemUser,
    UniqueModel,
)
from tests.testapp.models import (
    Name,
    Note,
    Permission as TAPermission,
    UniqueTestAppModel,
)


# Bad user defined collision resolvers:

class TestAppsOrderCR(AppsOrderCR):
    pass


class TestAppNameCR(AppNameCR):
    pass


def collision_resolver_which_is_not_class():
    pass


class CRNotExtendingFromBase:
    pass


class CRNoFunction(BaseCR):
    pass


class CRNoArguments(BaseCR):
    def resolve_collisions(self):
        pass


class CRBadResult(BaseCR):
    def resolve_collisions(self, namespace):
        return 1


class CRBadKey(BaseCR):
    def resolve_collisions(self, namespace):
        return {1: 'a'}


class CRBadValue(BaseCR):
    def resolve_collisions(self, namespace):
        return {'a': 1}


class CRBadTransformPath(PathBasedCR):
    def transform_import(self, module_path):
        return 1


class CRTestCase(TestCase):
    def setUp(self):
        super(CRTestCase, self).setUp()
        sys.stdout = six.StringIO()
        sys.stderr = six.StringIO()

    def get_all_names_for_model(self, model_to_find_occurences):
        result = set()
        for name, model_class in self.imported_objects.items():
            if model_class == model_to_find_occurences:
                result.add(name)
        return result

    def _assert_imported_under_names(self, model_class, names_under_model_is_available):
        self.assertSetEqual(self.get_all_names_for_model(model_class), names_under_model_is_available)
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

    def _assert_models_present_under_names(self, group, group_col, name, name_col, note, note_col, system_user,
                                           unique_model, permission, test_app_permission, unique_test_app_model):
        command = shell_plus.Command()
        self.imported_objects = command.get_imported_objects({})
        self.output = sys.stdout.getvalue()
        self._assert_imported_under_names(Group, group)
        self._assert_imported_under_names(Group_Col, group_col)
        self._assert_imported_under_names(Name, name)
        self._assert_imported_under_names(Name_Col, name_col)
        self._assert_imported_under_names(Note, note)
        self._assert_imported_under_names(Note_Col, note_col)
        self._assert_imported_under_names(SystemUser, system_user)
        self._assert_imported_under_names(UniqueModel, unique_model)
        self._assert_imported_under_names(Permission, permission)
        self._assert_imported_under_names(TAPermission, test_app_permission)
        self._assert_imported_under_names(UniqueTestAppModel, unique_test_app_model)

    def test_legacy_collision_resolver(self):
        self._assert_models_present_under_names(
            set(), {'Group'}, {'Name'}, set(), {'Note'}, set(), {'SystemUser'}, {'UniqueModel'}, set(), {'Permission'},
            {'UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.AppNamePrefixCR',
    )
    def test_app_name_prefix_collision_resolver(self):
        self._assert_models_present_under_names(
            {'django_contrib_auth_Group'}, {'tests_collisions_Group', 'Group'}, {'django_extensions_Name', 'Name'},
            {'tests_collisions_Name'}, {'django_extensions_Note', 'Note'}, {'tests_collisions_Note'}, {'SystemUser'},
            {'UniqueModel'}, {'django_contrib_auth_Permission'}, {'tests_testapp_Permission', 'Permission'},
            {'UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.AppNameSuffixCR',
    )
    def test_app_name_suffix_collision_resolver(self):
        self._assert_models_present_under_names(
            {'Group_django_contrib_auth'}, {'Group_tests_collisions', 'Group'}, {'Name_django_extensions', 'Name'},
            {'Name_tests_collisions'}, {'Note_django_extensions', 'Note'}, {'Note_tests_collisions'},
            {'SystemUser'}, {'UniqueModel'}, {'Permission_django_contrib_auth'},
            {'Permission_tests_testapp', 'Permission'}, {'UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.FullPathCR',
    )
    def test_full_path_collision_resolver(self):
        self._assert_models_present_under_names(
            {'django_contrib_auth_Group'}, {'tests_collisions_Group', 'Group'},
            {'tests_testapp_Name', 'Name'}, {'tests_collisions_Name'},
            {'tests_testapp_Note', 'Note'}, {'tests_collisions_Note'}, {'SystemUser'}, {'UniqueModel'},
            {'django_contrib_auth_Permission'},
            {'tests_testapp_Permission', 'Permission'}, {'UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.InstalledAppsOrderCR',
    )
    def test_installed_apps_order_collision_resolver(self):
        self._assert_models_present_under_names(
            {'Group'}, set(), set(), {'Name'}, set(), {'Note'}, {'SystemUser'}, {'UniqueModel'}, {'Permission'}, set(),
            {'UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='tests.management.commands.test_collision_resolver.TestAppsOrderCR',
    )
    def test_installed_bad_order_collision_resolver(self):
        with self.assertRaisesRegexp(AssertionError, "You must define APP_PRIORITIES in your resolver class!"):
            self._assert_models_present_under_names(
                set(), set(), set(), set(), set(), set(), set(), set(), set(), set(), set(),
            )

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='tests.management.commands.test_collision_resolver.TestAppNameCR',
    )
    def test_installed_apps_bad_name_collision_resolver(self):
        with self.assertRaisesRegexp(AssertionError, "You must define MODIFICATION_STRING in your resolver class!"):
            self._assert_models_present_under_names(
                set(), set(), set(), set(), set(), set(), set(), set(), set(), set(), set(),
            )

    def _assert_bad_resolver(self, message):
        with self.assertRaisesRegexp(AssertionError, message):
            self._assert_models_present_under_names(
                set(), set(), set(), set(), set(), set(), set(), set(), set(), set(), set(),
            )

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='tests.management.commands.test_collision_resolver.collision_resolver_which_is_not_class',
    )
    def test_installed_apps_not_class_collision_resolver(self):
        self._assert_bad_resolver("SHELL_PLUS_MODEL_IMPORTS_RESOLVER must be subclass of BaseCR!")

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='tests.management.commands.test_collision_resolver.CRNotExtendingFromBase',
    )
    def test_installed_apps_not_subclass_of_base(self):
        self._assert_bad_resolver("SHELL_PLUS_MODEL_IMPORTS_RESOLVER must be subclass of BaseCR!")

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='tests.management.commands.test_collision_resolver.CRNoFunction',
    )
    def test_installed_apps_no_resolve_conflicts_function(self):
        with self.assertRaisesRegexp(
            TypeError, "Can't instantiate abstract class CRNoFunction with abstract methods resolve_collisions"
        ):
            self._assert_models_present_under_names(
                set(), set(), set(), set(), set(), set(), set(), set(), set(), set(), set(),
            )

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='tests.management.commands.test_collision_resolver.CRNoArguments',
    )
    def test_installed_apps_no_arguments_resolve_conflicts(self):
        self._assert_bad_resolver("resolve_collisions function must take one argument!")

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='tests.management.commands.test_collision_resolver.CRBadResult',
    )
    def test_installed_apps_bad_result(self):
        self._assert_bad_resolver("Result of resolve_collisions function must be a dict!")

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='tests.management.commands.test_collision_resolver.CRBadKey',
    )
    def test_installed_apps_bad_key(self):
        self._assert_bad_resolver("key in collision resolver result should be str not 1")

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='tests.management.commands.test_collision_resolver.CRBadValue',
    )
    def test_installed_apps_bad_value(self):
        self._assert_bad_resolver("value in collision resolver result should be str not 1")

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='tests.management.commands.test_collision_resolver.CRBadTransformPath'
    )
    def test_bad_transform_path(self):
        self._assert_bad_resolver("result of transform_import must be str!")

    @override_settings(
        SHELL_PLUS_MODEL_ALIASES={'testapp': {'Note': 'MyFunnyNote'}},
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.AppNamePrefixCR',
    )
    def test_app_name_prefix_collision_resolver_with_model_alias(self):
        self._assert_models_present_under_names(
            {'django_contrib_auth_Group'}, {'tests_collisions_Group', 'Group'}, {'django_extensions_Name', 'Name'},
            {'tests_collisions_Name'}, {'MyFunnyNote'}, {'Note'}, {'SystemUser'},
            {'UniqueModel'}, {'django_contrib_auth_Permission'}, {'tests_testapp_Permission', 'Permission'},
            {'UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_MODEL_ALIASES={'testapp': {'Note': 'Name'}},
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.AppNamePrefixCR',
    )
    def test_app_name_prefix_collision_resolver_with_clash_because_of_model_alias(self):
        self._assert_models_present_under_names(
            {'django_contrib_auth_Group'}, {'tests_collisions_Group', 'Group'}, {'django_extensions_Name'},
            {'tests_collisions_Name'}, {'django_extensions_Note', 'Name'}, {'Note'}, {'SystemUser'},
            {'UniqueModel'}, {'django_contrib_auth_Permission'}, {'tests_testapp_Permission', 'Permission'},
            {'UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_APP_PREFIXES={'testapp': 'main_app'},
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.AppNamePrefixCR',
    )
    def test_app_name_prefix_collision_resolver_with_app_prefixes(self):
        self._assert_models_present_under_names(
            {'django_contrib_auth_Group'}, {'tests_collisions_Group', 'Group'}, {'main_app_Name'},
            {'Name'}, {'main_app_Note'}, {'Note'}, {'SystemUser'},
            {'UniqueModel'}, {'Permission'}, {'main_app_Permission'}, {'main_app_UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_APP_PREFIXES={'testapp': 'main_app', 'collisions': 'main_app'},
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.AppNamePrefixCR',
    )
    def test_app_name_prefix_collision_resolver_with_clashing_app_prefixes(self):
        self._assert_models_present_under_names(
            {'Group'}, {'main_app_Group'}, {'django_extensions_Name', 'main_app_Name'},
            {'tests_collisions_Name'}, {'django_extensions_Note', 'main_app_Note'},
            {'tests_collisions_Note'}, {'main_app_SystemUser'}, {'main_app_UniqueModel'}, {'Permission'},
            {'main_app_Permission'}, {'main_app_UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_APP_PREFIXES={'testapp': 'main_app', 'auth': 'main_app'},
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.AppNamePrefixCR',
    )
    def test_app_name_prefix_collision_resolver_clash_with_3rd_party(self):
        self._assert_models_present_under_names(
            {'main_app_Group'}, {'Group'}, {'main_app_Name'},
            {'Name'}, {'main_app_Note'}, {'Note'}, {'SystemUser'},
            {'UniqueModel'}, {'django_contrib_auth_Permission'}, {'main_app_Permission', 'tests_testapp_Permission'},
            {'main_app_UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_APP_PREFIXES={'testapp': 'testapp', 'auth': 'auth', 'collisions': 'collisions'},
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.AppNamePrefixCR',
    )
    def test_no_collisions_because_of_app_prefixes(self):
        self._assert_models_present_under_names(
            {'auth_Group'}, {'collisions_Group'}, {'testapp_Name'},
            {'collisions_Name'}, {'testapp_Note'}, {'collisions_Note'}, {'collisions_SystemUser'},
            {'collisions_UniqueModel'}, {'auth_Permission'}, {'testapp_Permission'},
            {'testapp_UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.AppNamePrefixCustomOrderCR',
    )
    def test_app_name_prefix_custom_order_collision_resolver(self):
        self._assert_models_present_under_names(
            {'django_contrib_auth_Group', 'Group'}, {'tests_collisions_Group'}, {'django_extensions_Name'},
            {'tests_collisions_Name', 'Name'}, {'django_extensions_Note'}, {'tests_collisions_Note', 'Note'},
            {'SystemUser'}, {'UniqueModel'}, {'django_contrib_auth_Permission', 'Permission'},
            {'tests_testapp_Permission'}, {'UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.AppNameSuffixCustomOrderCR',
    )
    def test_app_name_suffix_custom_order_collision_resolver(self):
        self._assert_models_present_under_names(
            {'Group_django_contrib_auth', 'Group'}, {'Group_tests_collisions'}, {'Name_django_extensions'},
            {'Name_tests_collisions', 'Name'}, {'Note_django_extensions'}, {'Note_tests_collisions', 'Note'},
            {'SystemUser'}, {'UniqueModel'}, {'Permission_django_contrib_auth', 'Permission'},
            {'Permission_tests_testapp'}, {'UniqueTestAppModel'},
        )

    @override_settings(
        SHELL_PLUS_MODEL_IMPORTS_RESOLVER='django_extensions.collision_resolvers.FullPathCustomOrderCR',
    )
    def test_full_path_custom_order_collision_resolver(self):
        self._assert_models_present_under_names(
            {'django_contrib_auth_Group', 'Group'}, {'tests_collisions_Group'},
            {'tests_testapp_Name'}, {'tests_collisions_Name', 'Name'},
            {'tests_testapp_Note'}, {'tests_collisions_Note', 'Note'}, {'SystemUser'}, {'UniqueModel'},
            {'django_contrib_auth_Permission', 'Permission'},
            {'tests_testapp_Permission'}, {'UniqueTestAppModel'},
        )
