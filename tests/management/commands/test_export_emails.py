# coding=utf-8
"""Module testing for manage.py export_emails command"""

from django.core.management import call_command

from django_extensions.management.commands.export_emails import Command

import pytest

from tests.testapp.settings import DATABASES


@pytest.fixture(scope='module')
def django_db_setup():
    """Select default database for testing"""
    settings.DATABASES = DATABASES


@pytest.fixture(scope='module')
def django_db_setup(django_db_setup, django_db_blocker):
    """Load to database a set of users, create for export emails command testing"""
    with django_db_blocker.unblock():
        call_command('loaddata', 'group.json')  # Loading initial data,testing, Group: Attendees.
        call_command('loaddata', 'user.json')   # Loading 20 users, initial data, testing.


@pytest.mark.django_db
def test_export_emails_noargs(capsys):
    """Test: python manage.py export_emails , without args.
        simple single entry per line in the format of:
            "full name" <my@address.com>;
    """
    export_emails = Command()
    export_emails.run_from_argv(
        ['manage.py', 'export_emails']
    )

    out, err = capsys.readouterr()


