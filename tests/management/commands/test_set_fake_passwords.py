# -*- coding: utf-8 -*-
from io import StringIO

import pytest
from django.contrib.auth.models import User
from django.core.management import CommandError, call_command

from django_extensions.management.commands.set_fake_passwords import DEFAULT_FAKE_PASSWORD

from unittest.mock import Mock, patch


@pytest.fixture(scope='module')
def django_db_setup(django_db_setup, django_db_blocker):
    """Load to database a set of users, create for export
    emails command testing"""
    with django_db_blocker.unblock():
        call_command('loaddata', 'group.json')
        call_command('loaddata', 'user.json')


@pytest.mark.django_db()
def test_without_args(capsys, settings):
    settings.DEBUG = True

    old_passwords = User.objects.values_list('password', flat=True).order_by('id')
    assert len(set(old_passwords)) == 3

    call_command('set_fake_passwords')
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

    call_command('set_fake_passwords', '--password=helloworld')
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
    with pytest.raises(CommandError, match="Only available in debug mode"):
        call_command('set_fake_passwords', verbosity=3, stdout=out, stderr=out)
