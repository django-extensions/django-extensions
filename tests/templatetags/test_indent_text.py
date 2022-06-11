# -*- coding: utf-8 -*-
from django.test import TestCase
from django.template import Context, Template, TemplateSyntaxError


class IndentByTagExceptions(TestCase):
    """Test for indentby exceptions."""

    def test_should_raise_TemplateSyntaxError_if_args_lenght_not_in_2_4(self):
        content = """{% load indent_text %}
{% indentby %}
Hello World
{% endindentby %}"""
        with self.assertRaisesRegex(TemplateSyntaxError, "indentby tag requires 1 or 3 arguments"):
            Template(content).render(Context())


class IndentByTagTests(TestCase):
    """Tests for indentby tag."""

    def test_should_add_4_spaces_indent_before_given_text(self):
        content = """{% load indent_text %}
{% indentby 4 %}
Hello World
{% endindentby %}"""
        expected_result = '\n    \n    Hello World\n'

        result = Template(content).render(Context())

        self.assertEqual(result, expected_result)

    def test_should_add_2_spaces_indent_before_given_text_if_statement_True(self):
        content = """{% load indent_text %}
{% indentby 2 if test_statement %}
Hello World
{% endindentby %}"""
        expected_result = '\n  \n  Hello World\n'

        result = Template(content).render(Context({'test_statement': True}))

        self.assertEqual(result, expected_result)

    def test_should_not_add_any_spaces_indent_before_given_text_if_statement_variable_does_not_exist(self):
        content = """{% load indent_text %}
{% indentby 2 if test_statement %}
Hello World
{% endindentby %}"""
        expected_result = '\n\nHello World\n'

        result = Template(content).render(Context())

        self.assertEqual(result, expected_result)
