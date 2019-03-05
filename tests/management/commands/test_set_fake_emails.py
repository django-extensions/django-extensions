# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import call_command, CommandError
from django.contrib.auth.models import User
from six import StringIO
from django_extensions.management.commands.set_fake_emails import Command

import pytest


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

    emails = User.objects.values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    generate_email = Command()
    generate_email.run_from_argv(['manage.py', 'set_fake_emails'])
    out, err = capsys.readouterr()
    assert 'Changed 3 emails' in out

    emails = User.objects.values_list('email', flat=True)
    assert all(email.endswith("@example.com") for email in emails)


@pytest.mark.django_db()
def test_no_admin(capsys, settings):
    settings.DEBUG = True

    emails = User.objects.values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    generate_email = Command()
    generate_email.run_from_argv(['manage.py', 'set_fake_emails', '-a'])
    out, err = capsys.readouterr()
    assert 'Changed 2 emails' in out

    emails = User.objects.filter(is_superuser=False).values_list('email', flat=True)
    assert all(email.endswith("@example.com") for email in emails)

    emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)


@pytest.mark.django_db()
def test_no_staff(capsys, settings):
    settings.DEBUG = True

    emails = User.objects.values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    generate_email = Command()
    generate_email.run_from_argv(['manage.py', 'set_fake_emails', '-s'])
    out, err = capsys.readouterr()
    assert 'Changed 2 emails' in out

    emails = User.objects.filter(is_staff=False).values_list('email', flat=True)
    assert all(email.endswith("@example.com") for email in emails)

    emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)


@pytest.mark.django_db()
def test_include_groups(capsys, settings):
    settings.DEBUG = True

    emails = User.objects.values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    generate_email = Command()
    generate_email.run_from_argv(['manage.py', 'set_fake_emails', '--include-groups=Attendees'])
    out, err = capsys.readouterr()
    assert 'Changed 2 emails' in out

    emails = User.objects.filter(is_superuser=False).values_list('email', flat=True)
    assert all(email.endswith("@example.com") for email in emails)

    emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)


@pytest.mark.django_db()
def test_include_groups_which_does_not_exists(capsys, settings):
    settings.DEBUG = True

    emails = User.objects.values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    with pytest.raises(CommandError, match='No groups matches filter: TEST'):
        call_command('set_fake_emails', '--include-groups=TEST')

    assert not User.objects.filter(email__endswith='@example.com').exists()


@pytest.mark.django_db()
def test_exclude_groups(capsys, settings):
    settings.DEBUG = True

    emails = User.objects.values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    generate_email = Command()
    generate_email.run_from_argv(['manage.py', 'set_fake_emails', '--exclude-groups=Attendees'])
    out, err = capsys.readouterr()
    assert 'Changed 1 emails' in out

    emails = User.objects.filter(is_superuser=False).values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
    assert all(email.endswith("@example.com") for email in emails)


@pytest.mark.django_db()
def test_exclude_groups_which_does_not_exists(capsys, settings):
    settings.DEBUG = True

    emails = User.objects.values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    with pytest.raises(CommandError, match='No groups matches filter: TEST'):
        call_command('set_fake_emails', '--exclude-groups=TEST')

    assert not User.objects.filter(email__endswith='@example.com').exists()


@pytest.mark.django_db()
def test_include_regexp(capsys, settings):
    settings.DEBUG = True

    emails = User.objects.values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    generate_email = Command()
    generate_email.run_from_argv(['manage.py', 'set_fake_emails', '--include=.*briel'])
    out, err = capsys.readouterr()
    assert 'Changed 1 emails' in out

    emails = User.objects.exclude(username="Gabriel").values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    emails = User.objects.filter(username="Gabriel").values_list('email', flat=True)
    assert all(email.endswith("@example.com") for email in emails)


@pytest.mark.django_db()
def test_exclude_regexp(capsys, settings):
    settings.DEBUG = True

    emails = User.objects.values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    generate_email = Command()
    generate_email.run_from_argv(['manage.py', 'set_fake_emails', '--exclude=.*briel'])
    out, err = capsys.readouterr()
    assert 'Changed 2 emails' in out

    emails = User.objects.filter(username="Gabriel").values_list('email', flat=True)
    assert all(email.endswith("@gmail.com") for email in emails)

    emails = User.objects.exclude(username="Gabriel").values_list('email', flat=True)
    assert all(email.endswith("@example.com") for email in emails)


def test_without_debug(settings):
    settings.DEBUG = False

    out = StringIO()
    with pytest.raises(CommandError, message="Only available in debug mod"):
        call_command('set_fake_emails', verbosity=3, stdout=out, stderr=out)
