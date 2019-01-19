from __future__ import unicode_literals

from django.core.management import CommandError, call_command
from django.test import TestCase

from django.utils.six import StringIO

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


class SyncDataTests(TestCase):
    """Tests for syncdata command."""

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_No_fixtures_found_if_fixture_labels_not_provided(self, m_stdout):  # noqa
        call_command('syncdata', verbosity=2)

        self.assertEqual('No fixtures found.\n', m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_No_fixtures_found_if_fixtures_not_found(self, m_stdout):  # noqa
        call_command('syncdata', 'foo', verbosity=2)

        self.assertIn('No fixtures found.\n', m_stdout.getvalue())
