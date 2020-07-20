# -*- coding: utf-8 -*-
from io import StringIO

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.test.utils import override_settings

from unittest.mock import patch


class SetDefaultSiteTests(TestCase):
    """Tests for set_default_site command."""

    @override_settings(SITE_ID=321)
    def test_should_raise_CommandError_when_Site_object_does_not_exist(self):
        with self.assertRaisesRegex(CommandError, "Default site with pk=321 does not exist"):
            call_command('set_default_site')

    @patch('django_extensions.management.commands.set_default_site.socket')
    def test_should_raise_CommandError_if_system_fqdn_return_None(self, m_socket):
        m_socket.getfqdn.return_value = None
        with self.assertRaisesRegex(CommandError, "Cannot find systems FQDN"):
            call_command('set_default_site', '--system-fqdn')

    def test_should_raise_CommandError_if_both_domain_and_set_as_system_fqdn_are_present(self):
        with self.assertRaisesRegex(CommandError, "The set_as_system_fqdn cannot be used with domain option."):
            call_command('set_default_site', '--domain=foo', '--system-fqdn')

    @override_settings(INSTALLED_APPS=[
        app for app in settings.INSTALLED_APPS
        if app != 'django.contrib.sites'])
    def test_should_raise_CommandError_Sites_framework_not_installed(self):
        with self.assertRaisesRegex(CommandError, "The sites framework is not installed."):
            call_command('set_default_site', '--domain=foo', '--system-fqdn')

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_print_Nothing_to_update(self, m_stdout):
        call_command('set_default_site')

        self.assertIn("Nothing to update (need --name, --domain and/or --system-fqdn)\n", m_stdout.getvalue())

    @patch('django_extensions.management.commands.set_default_site.socket')
    def test_should_use_domain_as_name_if_system_fqdn_return_domain_and_name_is_not_provided(self, m_socket):
        m_socket.getfqdn.return_value = 'test.com'

        call_command('set_default_site', '--system-fqdn')
        result = Site.objects.get(pk=settings.SITE_ID)

        self.assertEqual(result.name, 'test.com')
        self.assertEqual(result.domain, 'test.com')

    @patch('django_extensions.management.commands.set_default_site.socket')
    def test_should_set_custom_nameif_system_fqdn_return_domain_and_name_is_provided(self, m_socket):
        m_socket.getfqdn.return_value = 'test.com'

        call_command('set_default_site', '--system-fqdn', '--name=foo')
        result = Site.objects.get(pk=settings.SITE_ID)

        self.assertEqual(result.name, 'foo')
        self.assertEqual(result.domain, 'test.com')

    def test_should_set_name_and_domain_if_provided(self):
        call_command('set_default_site', '--name=foo', '--domain=bar')
        result = Site.objects.get(pk=settings.SITE_ID)

        self.assertEqual(result.name, 'foo')
        self.assertEqual(result.domain, 'bar')

    def test_should_set_name_only(self):
        call_command('set_default_site', '--name=foo')
        result = Site.objects.get(pk=settings.SITE_ID)

        self.assertEqual(result.name, 'foo')
        self.assertEqual(result.domain, 'example.com')

    def test_should_set_domain_only(self):
        call_command('set_default_site', '--domain=bar')
        result = Site.objects.get(pk=settings.SITE_ID)

        self.assertEqual(result.name, 'example.com')
        self.assertEqual(result.domain, 'bar')
