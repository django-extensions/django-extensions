# -*- coding: utf-8 -*-
from io import StringIO

from django.conf.urls import url
from django.core.management import CommandError, call_command
from django.http import HttpResponse
from django.test import TestCase
from django.test.utils import override_settings
from django.views.generic.base import View

from unittest.mock import Mock, patch


def function_based_view(request):
    pass


class ClassView(View):
    pass


urlpatterns = [
    url(r'lambda/view', lambda request: HttpResponse('OK')),
    url(r'function/based/', function_based_view, name='function-based-view'),
    url(r'class/based/', ClassView.as_view(), name='class-based-view'),
]


class ShowUrlsExceptionsTests(TestCase):
    """Tests if show_urls command raises exceptions."""

    def test_should_raise_CommandError_when_format_style_does_not_exists(self):
        with self.assertRaisesRegex(CommandError, "Format style 'invalid_format' does not exist. Options: aligned, dense, json, pretty-json, table, verbose"):
            call_command('show_urls', '--format=invalid_format')

    def test_should_raise_CommandError_when_doesnt_have_urlconf_attr(self):
        with self.assertRaisesRegex(CommandError, "Settings module <Settings \"tests.testapp.settings\"> does not have the attribute INVALID_URLCONF."):
            call_command('show_urls', '--urlconf=INVALID_URLCONF')

    @override_settings(INVALID_URLCONF='')
    def test_should_raise_CommandError_when_doesnt_have_urlconf_attr_print_exc(self):
        m_traceback = Mock()
        with self.assertRaisesRegex(CommandError, 'Error occurred while trying to load : Empty module name'):
            with patch.dict('sys.modules', traceback=m_traceback):
                call_command('show_urls', '--urlconf=INVALID_URLCONF', '--traceback')

        self.assertTrue(m_traceback.print_exc.called)


@override_settings(ROOT_URLCONF='tests.management.commands.test_show_urls')
class ShowUrlsTests(TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_show_urls_unsorted_but_same_order_as_found_in_url_patterns(self, m_stdout):
        call_command('show_urls', '-u', verbosity=3)

        lines = m_stdout.getvalue().splitlines()
        self.assertIn('/lambda/view\ttests.management.commands.test_show_urls.<lambda>', lines[0])
        self.assertIn('/function/based/\ttests.management.commands.test_show_urls.function_based_view\tfunction-based-view', lines[1])
        self.assertIn('/class/based/\ttests.management.commands.test_show_urls.ClassView\tclass-based-view', lines[2])

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_show_urls_sorted_alphabetically(self, m_stdout):
        call_command('show_urls', verbosity=3)

        lines = m_stdout.getvalue().splitlines()
        self.assertEqual('/class/based/\ttests.management.commands.test_show_urls.ClassView\tclass-based-view', lines[0])
        self.assertEqual('/function/based/\ttests.management.commands.test_show_urls.function_based_view\tfunction-based-view', lines[1])
        self.assertEqual('/lambda/view\ttests.management.commands.test_show_urls.<lambda>', lines[2])

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_show_urls_in_json_format(self, m_stdout):
        call_command('show_urls', '--format=json')

        self.assertJSONEqual(m_stdout.getvalue(), [
            {"url": "/lambda/view", "module": "tests.management.commands.test_show_urls.<lambda>", "name": "", "decorators": ""},
            {"url": "/function/based/", "module": "tests.management.commands.test_show_urls.function_based_view", "name": "function-based-view", "decorators": ""},
            {"url": "/class/based/", "module": "tests.management.commands.test_show_urls.ClassView", "name": "class-based-view", "decorators": ""}
        ])
        self.assertEqual(len(m_stdout.getvalue().splitlines()), 1)

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_show_urls_in_pretty_json_format(self, m_stdout):
        call_command('show_urls', '--format=pretty-json')

        self.assertJSONEqual(m_stdout.getvalue(), [
            {"url": "/lambda/view", "module": "tests.management.commands.test_show_urls.<lambda>", "name": "", "decorators": ""},
            {"url": "/function/based/", "module": "tests.management.commands.test_show_urls.function_based_view", "name": "function-based-view", "decorators": ""},
            {"url": "/class/based/", "module": "tests.management.commands.test_show_urls.ClassView", "name": "class-based-view", "decorators": ""}
        ])
        self.assertEqual(len(m_stdout.getvalue().splitlines()), 20)

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_show_urls_in_table_format(self, m_stdout):
        call_command('show_urls', '--format=table')

        self.assertIn('/class/based/    | tests.management.commands.test_show_urls.ClassView           | class-based-view    |', m_stdout.getvalue())
        self.assertIn('/function/based/ | tests.management.commands.test_show_urls.function_based_view | function-based-view |', m_stdout.getvalue())
        self.assertIn('/lambda/view     | tests.management.commands.test_show_urls.<lambda>            |                     |', m_stdout.getvalue())

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_show_urls_in_aligned_format(self, m_stdout):
        call_command('show_urls', '--format=aligned')

        lines = m_stdout.getvalue().splitlines()
        self.assertEqual('/class/based/      tests.management.commands.test_show_urls.ClassView             class-based-view      ', lines[0])
        self.assertEqual('/function/based/   tests.management.commands.test_show_urls.function_based_view   function-based-view   ', lines[1])
        self.assertEqual('/lambda/view       tests.management.commands.test_show_urls.<lambda>                                    ', lines[2])

    @patch('sys.stdout', new_callable=StringIO)
    def test_should_show_urls_with_no_color_option(self, m_stdout):
        call_command('show_urls', '--no-color')

        lines = m_stdout.getvalue().splitlines()
        self.assertEqual('/class/based/\ttests.management.commands.test_show_urls.ClassView\tclass-based-view', lines[0])
        self.assertEqual('/function/based/\ttests.management.commands.test_show_urls.function_based_view\tfunction-based-view', lines[1])
        self.assertEqual('/lambda/view\ttests.management.commands.test_show_urls.<lambda>', lines[2])
