# -*- coding: utf-8 -*-
from django.core.management import call_command
from unittest import mock


def test_initialize_mail_server():
    with mock.patch('django_extensions.management.commands.mail_debug.asyncore.loop') as loop:
        call_command('mail_debug')
        assert loop.called, 'asyncore.loop was not called'
