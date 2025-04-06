# -*- coding: utf-8 -*-
from django.core.management import call_command
from unittest import mock


def test_initialize_mail_server():
    with mock.patch(
        "django_extensions.management.commands.mail_debug.asyncio"
    ) as asyncio:
        call_command("mail_debug", "2525")
        assert asyncio.get_event_loop.called, "asyncio.get_event_loop was not called"
