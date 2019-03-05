# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import pytest
from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from six import StringIO

from django_extensions.management.commands.set_fake_passwords import DEFAULT_FAKE_PASSWORD, Command

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch


@pytest.fixture(scope='module')  # noqa
def django_db_setup(django_db_setup, django_db_blocker):  # noqa
    """Load to database a set of users, create for export
    emails command testing"""
    with django_db_blocker.unblock():  # noqa
        call_command('loaddata', 'group.json')
        call_command('loaddata', 'user.json')


@pytest.mark.django_db()
def test_without_args(capsys, settings):
    settings.DEBUG = True

    old_passwords = User.objects.values_list('password', flat=True).order_by('id')
    assert len(set(old_passwords)) == 3

    generate_password = Command()
    generate_password.run_from_argv(['manage.py', 'set_fake_passwords'])
    out, err = capsys.readouterr()
    assert 'Reset 3 passwords' in out

    new_passwords = User.objects.values_list('password', flat=True).order_by('id')
    assert len(set(new_passwords)) == 1
    assert old_passwords != new_passwords

    for user in User.objects.all():
        assert user.check_password(DEFAULT_FAKE_PASSWORD)


@pytest.mark.django_db()
def test_with_password(capsys, settings):
    settings.DEBUG = True

    generate_password = Command()
    generate_password.run_from_argv(['manage.py', 'set_fake_passwords', '--password=helloworld'])
    out, err = capsys.readouterr()
    assert 'Reset 3 passwords' in out

    for user in User.objects.all():
        assert user.check_password("helloworld")


@pytest.mark.django_db()
def test_with_prompt(settings):
    settings.DEBUG = True

    m_getpass = Mock()
    m_getpass.getpass.return_value = 'test'

    with patch.dict('sys.modules', getpass=m_getpass):
        call_command('set_fake_passwords', '--prompt')

    assert all([user.check_password("test") for user in User.objects.all()])


@pytest.mark.django_db()
def test_with_prompt_with_empty_password(settings):
    settings.DEBUG = True

    m_getpass = Mock()
    m_getpass.getpass.return_value = None

    with pytest.raises(CommandError, match='You must enter a valid password'):
        with patch.dict('sys.modules', getpass=m_getpass):
            call_command('set_fake_passwords', '--prompt')


def test_without_debug(settings):
    settings.DEBUG = False

    out = StringIO()
    with pytest.raises(CommandError, message="Only available in debug mod"):
        call_command('set_fake_passwords', verbosity=3, stdout=out, stderr=out)
