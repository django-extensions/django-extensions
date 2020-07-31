# -*- coding: utf-8 -*-
from importlib import import_module
from io import StringIO

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase

from unittest.mock import patch


class PrintUserForSessionExceptionsTests(TestCase):
    """Test if print_user_for_session command raises exception."""

    def test_should_raise_CommandError_if_session_key_contains_exclamination_mark(self):
        with self.assertRaisesRegex(CommandError, 'malformed session key'):
            call_command('print_user_for_session', 'l6hxnwblpvrfu8bohelmqjj4soyo2r!?')


class PrintUserForSessionTests(TestCase):
    """Test for print_user_for_session command."""

    def setUp(self):
        self.engine = import_module(settings.SESSION_ENGINE)

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_Session_Key_does_not_exist_or_expired(self, m_stdout):
        call_command('print_user_for_session', 'l6hxnwblpvrfu8bohelmqjj4soyo2r12')

        self.assertIn('Session Key does not exist. Expired?', m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_that_there_is_no_user_associated_with_given_session(self, m_stdout):
        session = self.engine.SessionStore()
        session.update({
            '_auth_user_backend': 'django.contrib.auth.backends.ModelBackend',
            '_auth_user_hash': 'b67352fde8582b12f068c10fd9d29f9fa1af0459',
        })
        session.create()

        call_command('print_user_for_session', session.session_key)

        self.assertIn('No user associated with session', m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_that_there_is_no_backend_associated_with_given_session(self, m_stdout):
        session = self.engine.SessionStore()
        session.update({
            '_auth_user_id': 1234,
            '_auth_user_hash': 'b67352fde8582b12f068c10fd9d29f9fa1af0459',
        })
        session.create()

        call_command('print_user_for_session', session.session_key)

        self.assertIn('No authentication backend associated with session', m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_that_there_is_no_user_associated_with_id(self, m_stdout):
        session = self.engine.SessionStore()
        session.update({
            '_auth_user_id': 1234,
            '_auth_user_backend': 'django.contrib.auth.backends.ModelBackend',
            '_auth_user_hash': 'b67352fde8582b12f068c10fd9d29f9fa1af0459',
        })
        session.create()

        call_command('print_user_for_session', session.session_key)

        self.assertIn('No user associated with that id.', m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_user_info_for_session(self, m_stdout):
        user = get_user_model().objects.create(first_name='John', last_name='Doe', username='foobar', email='foo@bar.com')
        session = self.engine.SessionStore()
        session.update({
            '_auth_user_id': user.pk,
            '_auth_user_backend': 'django.contrib.auth.backends.ModelBackend',
            '_auth_user_hash': 'b67352fde8582b12f068c10fd9d29f9fa1af0459',
        })
        session.create()
        expected_out = """User id: {}
full name: John Doe
short name: John
username: foobar
email: foo@bar.com
""".format(user.pk)

        call_command('print_user_for_session', session.session_key)

        self.assertIn(expected_out, m_stdout.getvalue())
