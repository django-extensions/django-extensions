# -*- coding: utf-8 -*-
from django.core import mail
from django.core.management import call_command
from django.test import TestCase
from django.test.utils import override_settings
from io import StringIO

from unittest.mock import patch


class EmailNotificationCommandTests(TestCase):
    """Tests for EmailNotificationCommand class."""

    @override_settings(ADMINS=[])
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_that_no_email_recipients_available(self, m_stdout):
        with self.assertRaises(Exception):
            call_command('test_email_notification_command',
                         '--email-exception', verbosity=2)

        self.assertIn('No email recipients available', m_stdout.getvalue())
        self.assertListEqual(mail.outbox, [])

    @override_settings(ADMINS=['foo@bar.com', 'bar@foo.com'],
                       DEFAULT_FROM_EMAIL='webmaster@foo.bar')
    def test_should_send_email_with_command_name_and_full_traceback_if_command_fail(self):
        expected_lines = '''Reporting execution of command: 'test_email_notification_command'
Traceback:
    raise Exception()'''

        with self.assertRaises(Exception):
            call_command('test_email_notification_command',
                         '--email-exception', verbosity=2)

        self.assertIsNot(mail.outbox, [])
        self.assertEqual(mail.outbox[0].subject, 'Django extensions email notification.')
        self.assertEqual(mail.outbox[0].from_email, 'webmaster@foo.bar')
        self.assertListEqual(mail.outbox[0].to, ['foo@bar.com', 'bar@foo.com'])
        for expected_line in expected_lines.splitlines():
            self.assertIn(expected_line, mail.outbox[0].body)

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_not_notify_if_notification_level_is_not_set(self, m_stdout):
        call_command('runscript', 'sample_script', '--email-notifications', verbosity=2)

        self.assertIn("Exiting, not in 'notify always' mode", m_stdout.getvalue())
        self.assertListEqual(mail.outbox, [])

    @override_settings(ADMINS=['foo@bar.com'],
                       DEFAULT_FROM_EMAIL='webmaster@foo.bar',
                       EMAIL_NOTIFICATIONS={
                           'tests.testapp.scripts.sample_script': {
                               'subject': 'my_script subject',
                               'body': 'my_script body',
                               'from_email': 'from_email@example.com',
                               'recipients': ('recipient0@example.com',),
                               'no_admins': False,
                               'no_traceback': False,
                               'notification_level': 1,
                               'fail_silently': False
                           }})
    def test_should_notify_if_notification_level_is_greater_than_0(self):
        call_command('runscript', 'sample_script', '--email-notifications', verbosity=2)

        self.assertIsNot(mail.outbox, [])
        self.assertEqual(mail.outbox[0].subject, 'my_script subject')
        self.assertEqual(mail.outbox[0].body, 'my_script body')
        self.assertEqual(mail.outbox[0].from_email, 'from_email@example.com')
        self.assertListEqual(mail.outbox[0].to, ['recipient0@example.com', 'foo@bar.com'])
