# -*- coding: utf-8 -*-
from distutils.version import LooseVersion
from io import StringIO

import pytest
from django import get_version
from django.core.management import call_command
from django.test import TestCase

from unittest.mock import patch


class GenerateSecretKeyTests(TestCase):
    """Tests for generate_secret_key command."""

    @patch('django_extensions.management.commands.generate_secret_key.get_random_secret_key')
    @patch('sys.stdout', new_callable=StringIO)
    def test_should_return_random_secret_key(self, m_stdout, m_get_random_secret):
        m_get_random_secret.return_value = 'random_secret_key'

        call_command('generate_secret_key')

        self.assertIn('random_secret_key', m_stdout.getvalue())
