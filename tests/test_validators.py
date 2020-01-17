# -*- coding: utf-8 -*-
from django.core.exceptions import ValidationError
from django.test import TestCase

from django_extensions.validators import NoControlCharactersValidator, NoWhitespaceValidator


class NoControlCharactersValidatorTests(TestCase):
    """Tests for NoControlCharactersValidator."""

    def test_should_raise_default_message_and_code_if_value_contains_new_line(self):
        self.validator = NoControlCharactersValidator()
        value_with_new_line = 'test\nvalue'

        with self.assertRaises(ValidationError) as cm:
            self.validator(value_with_new_line)

        self.assertEqual(cm.exception.message, 'Control Characters like new lines or tabs are not allowed.')
        self.assertEqual(cm.exception.code, 'no_control_characters')
        self.assertDictEqual(cm.exception.params, {'value': value_with_new_line, 'whitelist': None})

    def test_should_raise_custom_message_and_code_if_value_contains_tabs(self):
        self.validator = NoControlCharactersValidator(message='custom message', code='custom code')
        value_with_tabs = 'test\tvalue'

        with self.assertRaises(ValidationError) as cm:
            self.validator(value_with_tabs)

        self.assertEqual(cm.exception.message, 'custom message')
        self.assertEqual(cm.exception.code, 'custom code')
        self.assertDictEqual(cm.exception.params, {'value': value_with_tabs, 'whitelist': None})

    def test_should_not_raise_if_value_contains_characters_which_is_on_whitelist(self):
        self.validator = NoControlCharactersValidator(message='custom message', code='custom code', whitelist=['\n'])
        value_with_new_line = 'test\nvalue'

        result = self.validator(value_with_new_line)

        self.assertIsNone(result)


class NoWhiteSpaceValidatorTests(TestCase):
    """Tests for NoWhitespaceValidator."""

    def test_should_raise_default_message_and_code_if_value_has_leading_whitespace(self):
        self.validator = NoWhitespaceValidator()

        value_with_leading_whitespace = ' test_value'

        with self.assertRaises(ValidationError) as cm:
            self.validator(value_with_leading_whitespace)

        self.assertEqual(cm.exception.message, 'Leading and Trailing whitespaces are not allowed.')
        self.assertEqual(cm.exception.code, 'no_whitespace')
        self.assertDictEqual(cm.exception.params, {'value': value_with_leading_whitespace})

    def test_should_raise_custom_message_and_code_if_value_has_trailing_whitespace(self):
        self.validator = NoWhitespaceValidator(message='custom message', code='custom code')
        value_with_trailing_whitespace = 'test value '

        with self.assertRaises(ValidationError) as cm:
            self.validator(value_with_trailing_whitespace)

        self.assertEqual(cm.exception.message, 'custom message')
        self.assertEqual(cm.exception.code, 'custom code')
        self.assertDictEqual(cm.exception.params, {'value': value_with_trailing_whitespace})

    def test_should_not_raise_if_value_doesnt_have_leading_or_trailing_whitespaces(self):
        self.validator = NoWhitespaceValidator()
        value_without_leading_or_trailing_whitespaces = 'test value'

        result = self.validator(value_without_leading_or_trailing_whitespaces)

        self.assertIsNone(result)
