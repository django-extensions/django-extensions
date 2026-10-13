import os

from unittest.mock import patch

from django.apps import apps
from django.core.management import CommandError, call_command
from django.db import models
from django.test import TestCase, override_settings
from tests import testapp_with_appconfig

MIGRATIONS_DIR = os.path.join(testapp_with_appconfig.__path__[0], "migrations")
SQUASHED_MIGRATION = "0001_squashed_0002_namemodel.py"


@override_settings(MIGRATION_MODULES={"testapp_with_appconfig": "tests.testapp_with_appconfig.migrations"})
class BaseDeleteSquashedMigrationsTestCase(TestCase):
    def migration_exists(self, filename):
        return os.path.exists(os.path.join(MIGRATIONS_DIR, filename))

    def read_migration(self, filename):
        with open(os.path.join(MIGRATIONS_DIR, filename)) as fp:
            return fp.read()

    def write_migration(self, filename, content):
        with open(os.path.join(MIGRATIONS_DIR, filename), "w") as fp:
            fp.write(content)

    def setUp(self):
        # Models declared inside the tests end up in the global app registry.
        # Remember what was registered so tearDown can restore it, otherwise the
        # models leak into the following tests and their migrations.
        self._registered_models = dict(apps.all_models["testapp_with_appconfig"])

        class TitleModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            title = models.CharField(max_length=50)

            class Meta:
                app_label = "testapp_with_appconfig"

        call_command("makemigrations", "testapp_with_appconfig")

    def tearDown(self):
        registered_models = apps.all_models["testapp_with_appconfig"]
        registered_models.clear()
        registered_models.update(self._registered_models)
        apps.clear_cache()

        for root, dirs, files in os.walk(MIGRATIONS_DIR):
            for filename in files:
                if filename.startswith("000"):
                    os.remove(os.path.join(root, filename))

    def make_squashed_migration(self):
        class NameModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            name = models.CharField(max_length=50)

            class Meta:
                app_label = "testapp_with_appconfig"

        call_command("makemigrations", "testapp_with_appconfig")
        call_command("squashmigrations", "testapp_with_appconfig", "0002", "--noinput")


class DeleteSquashedMigrationsExceptionsTests(BaseDeleteSquashedMigrationsTestCase):
    """Tests for delete_squashed_migrations command exceptions."""

    def test_should_raise_CommandError_if_app_does_not_have_migrations(self):
        with self.assertRaisesRegex(
            CommandError,
            r"App 'testapp_with_no_models_file' does not have migrations \(so delete_squashed_migrations on it makes no sense\)",
        ):
            call_command("delete_squashed_migrations", "testapp_with_no_models_file")

    def test_should_raise_CommandEror_if_migration_is_not_squashed(self):
        with self.assertRaisesRegex(
            CommandError,
            "The migration testapp_with_appconfig 0001_initial is not a squashed migration.",
        ):
            call_command("delete_squashed_migrations", "testapp_with_appconfig", "0001")

    def test_should_raise_CommandEror_if_more_than_one_migration_matches_to_given_arg(
        self,
    ):
        self.make_squashed_migration()

        with self.assertRaisesRegex(
            CommandError,
            "More than one migration matches '0001' in app 'testapp_with_appconfig'. Please be more specific.",
        ):
            call_command("delete_squashed_migrations", "testapp_with_appconfig", "0001")

    def test_should_raise_CommandEror_if_squashed_migration_not_found(self):
        class NameModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            name = models.CharField(max_length=50)

            class Meta:
                app_label = "testapp_with_appconfig"

        call_command("makemigrations", "testapp_with_appconfig")

        with self.assertRaisesRegex(
            CommandError,
            "Cannot find a squashed migration in app 'testapp_with_appconfig'.",
        ):
            call_command("delete_squashed_migrations", "testapp_with_appconfig")

    def test_should_raise_CommandEror_if_squashed_migration_not_foundee(self):
        with self.assertRaisesRegex(
            CommandError,
            "Cannot find a migration matching '0002' from app 'testapp_with_appconfig'.",
        ):
            call_command("delete_squashed_migrations", "testapp_with_appconfig", "0002")

    def test_should_raise_CommandError_when_database_does_not_exist(self):
        with self.assertRaisesRegex(CommandError, "Unknown database non-existing_database"):
            call_command(
                "delete_squashed_migrations",
                "testapp_with_appconfig",
                "--database=non-existing_database",
            )

    def test_should_raise_CommandError_when_replaces_cannot_be_found(self):
        self.make_squashed_migration()
        content = self.read_migration(SQUASHED_MIGRATION)
        # Rewrite "replaces" in a shape the command does not know how to clean up.
        content = content.replace("replaces = [", "replaces = list([").replace("    ]\n\n    initial", "    ])\n\n    initial")
        self.assertIn("replaces = list([", content)
        self.write_migration(SQUASHED_MIGRATION, content)

        with self.assertRaisesRegex(CommandError, "Couldn't find 'replaces =' lines in file"):
            call_command("delete_squashed_migrations", "testapp_with_appconfig", interactive=False)

        # The replaced migrations are gone, the squashed file is left untouched.
        self.assertFalse(self.migration_exists("0001_initial.py"))
        self.assertFalse(self.migration_exists("0002_namemodel.py"))
        self.assertEqual(self.read_migration(SQUASHED_MIGRATION), content)


class DeleteSquashedMigrationsTests(BaseDeleteSquashedMigrationsTestCase):
    """Tests for delete_squashed_migrations command."""

    def assertReplacesRemoved(self, content):
        self.assertNotIn("replaces", content)
        self.assertIn("    initial = True\n", content)
        # Exactly one blank line is kept between the class line and the next
        # attribute, no extra empty line is left where "replaces" used to be.
        self.assertIn("class Migration(migrations.Migration):\n\n    initial", content)
        self.assertNotIn("\n\n\n    ", content)

    @patch("builtins.input")
    def test_should_delete_squashed_migrations(self, m_input):
        m_input.return_value = "y"

        self.make_squashed_migration()
        call_command("delete_squashed_migrations", "testapp_with_appconfig")

        self.assertEqual(m_input.call_count, 2)
        self.assertFalse(self.migration_exists("0001_initial.py"))
        self.assertFalse(self.migration_exists("0002_namemodel.py"))
        self.assertTrue(self.migration_exists(SQUASHED_MIGRATION))
        self.assertReplacesRemoved(self.read_migration(SQUASHED_MIGRATION))

    def test_should_delete_squashed_migrations_if_interactive_mode_is_set_to_False(
        self,
    ):
        self.make_squashed_migration()
        call_command("delete_squashed_migrations", "testapp_with_appconfig", interactive=False)

        self.assertFalse(self.migration_exists("0001_initial.py"))
        self.assertFalse(self.migration_exists("0002_namemodel.py"))
        self.assertTrue(self.migration_exists(SQUASHED_MIGRATION))
        self.assertReplacesRemoved(self.read_migration(SQUASHED_MIGRATION))

    def test_should_remove_single_line_replaces(self):
        self.make_squashed_migration()
        content = self.read_migration(SQUASHED_MIGRATION)
        content = content.replace(
            "    replaces = [\n"
            '        ("testapp_with_appconfig", "0001_initial"),\n'
            '        ("testapp_with_appconfig", "0002_namemodel"),\n'
            "    ]\n",
            '    replaces = [("testapp_with_appconfig", "0001_initial"), ("testapp_with_appconfig", "0002_namemodel")]\n',
        )
        self.assertIn('replaces = [("testapp_with_appconfig"', content)
        self.write_migration(SQUASHED_MIGRATION, content)

        call_command("delete_squashed_migrations", "testapp_with_appconfig", interactive=False)

        self.assertReplacesRemoved(self.read_migration(SQUASHED_MIGRATION))

    def test_should_remove_replaces_without_preceding_blank_line(self):
        self.make_squashed_migration()
        content = self.read_migration(SQUASHED_MIGRATION)
        content = content.replace(
            "class Migration(migrations.Migration):\n\n    replaces",
            "class Migration(migrations.Migration):\n    replaces",
        )
        self.assertIn("Migration):\n    replaces", content)
        self.write_migration(SQUASHED_MIGRATION, content)

        call_command("delete_squashed_migrations", "testapp_with_appconfig", interactive=False)

        self.assertReplacesRemoved(self.read_migration(SQUASHED_MIGRATION))

    @patch("builtins.input")
    def test_should_not_delete_anything(self, m_input):
        m_input.return_value = None

        self.make_squashed_migration()
        content = self.read_migration(SQUASHED_MIGRATION)
        call_command("delete_squashed_migrations", "testapp_with_appconfig")

        self.assertTrue(self.migration_exists("0001_initial.py"))
        self.assertTrue(self.migration_exists("0002_namemodel.py"))
        self.assertTrue(self.migration_exists(SQUASHED_MIGRATION))
        self.assertEqual(self.read_migration(SQUASHED_MIGRATION), content)

    @patch("builtins.input")
    def test_should_not_modify_squashed_migration_when_declined(self, m_input):
        m_input.side_effect = ["y", "n"]

        self.make_squashed_migration()
        content = self.read_migration(SQUASHED_MIGRATION)
        call_command("delete_squashed_migrations", "testapp_with_appconfig")

        self.assertFalse(self.migration_exists("0001_initial.py"))
        self.assertFalse(self.migration_exists("0002_namemodel.py"))
        self.assertEqual(self.read_migration(SQUASHED_MIGRATION), content)

    def test_should_not_change_anything_in_dry_run_mode(self):
        self.make_squashed_migration()
        content = self.read_migration(SQUASHED_MIGRATION)
        call_command(
            "delete_squashed_migrations",
            "testapp_with_appconfig",
            interactive=False,
            dry_run=True,
        )

        self.assertTrue(self.migration_exists("0001_initial.py"))
        self.assertTrue(self.migration_exists("0002_namemodel.py"))
        self.assertEqual(self.read_migration(SQUASHED_MIGRATION), content)

    def test_should_not_delete_files_for_given_squashed_migration(self):
        self.make_squashed_migration()

        class FooModel(models.Model):
            created_at = models.DateTimeField(auto_now_add=True)
            name = models.CharField(max_length=50)

            class Meta:
                app_label = "testapp_with_appconfig"

        call_command("makemigrations", "testapp_with_appconfig")
        self.assertTrue(self.migration_exists("0003_foomodel.py"))

        call_command(
            "delete_squashed_migrations",
            "testapp_with_appconfig",
            "0001_squashed_0002_namemodel",
            interactive=False,
        )

        self.assertFalse(self.migration_exists("0001_initial.py"))
        self.assertFalse(self.migration_exists("0002_namemodel.py"))
        self.assertTrue(self.migration_exists(SQUASHED_MIGRATION))
        self.assertTrue(self.migration_exists("0003_foomodel.py"))
        self.assertReplacesRemoved(self.read_migration(SQUASHED_MIGRATION))
