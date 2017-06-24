# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import call_command

from django_extensions.management.commands.export_emails import Command

import pytest

from tests.testapp.settings import DATABASES


@pytest.fixture(autouse=True)
def custom_djsettings(settings):  # noqa
    """Custom django settings to avoid warnings in stdout"""
    settings.TEMPLATE_DEBUG = False
    settings.DEBUG = False
    return settings


@pytest.fixture(scope='module')
def django_db_setup():  # noqa
    """Select default database for testing"""
    settings.DATABASES = DATABASES  # noqa


@pytest.fixture(scope='module')  # noqa
def django_db_setup(django_db_setup, django_db_blocker):  # noqa
    """Load to database a set of users, create for export
    emails command testing"""
    with django_db_blocker.unblock():  # noqa
        call_command('loaddata', 'group.json')
        call_command('loaddata', 'user.json')


@pytest.mark.django_db()
def test_do_export_emails_stdout_start(capsys):
    """Testing export_emails command without args.stdout starts."""
    export_emails = Command()
    export_emails.run_from_argv(
        ['manage.py', 'export_emails']
    )

    out, err = capsys.readouterr()
    assert out.startswith('"Mijaíl Bulgakóv')


@pytest.mark.django_db()
def test_do_export_emails_stdout_end(capsys):
    """Testing export_emails command without args.stdout end."""
    export_emails = Command()
    export_emails.run_from_argv(['manage.py', 'export_emails'])

    out, err = capsys.readouterr()
    assert '"Frédéric Mistral" <frederic_mistral@gmail.com>;\n\n' in out


@pytest.mark.django_db()
def test_do_export_emails_format_email(capsys):
    """Testing python.manage export_emails -f emails"""
    export_emails = Command()
    export_emails.run_from_argv(['manage.py', 'export_emails', '--format=emails'])

    out, err = capsys.readouterr()
    assert 'frederic_mistral@gmail.com' in out


@pytest.mark.django_db()
def test_do_export_emails_format_google(capsys):
    """Testing python.manage export_emails -f google"""
    export_emails = Command()
    export_emails.run_from_argv(['manage.py', 'export_emails', '--format=google'])

    out, err = capsys.readouterr()
    assert out.startswith('Name,Email')
