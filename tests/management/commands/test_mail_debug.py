# -*- coding: utf-8 -*-
import mock
from django_extensions.management.commands import mail_debug


def test_initialize_mail_server():
    with mock.patch('django_extensions.management.commands.mail_debug.asyncore.loop') as loop:
        command = mail_debug.Command()
        command.run_from_argv(['manage.py', 'mail_debug'])
        assert loop.called, 'asyncore.loop was not called'
