# -*- coding: utf-8 -*-
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import TestCase, SimpleTestCase

from django_extensions.validators import (
    NoControlCharactersValidator,
    NoWhitespaceValidator,
    HexValidator,
)


class NoControlCharactersValidatorTests(TestCase):
    """Tests for NoControlCharactersValidator."""

    def test_should_raise_default_message_and_code_if_value_contains_new_line(self):
        self.validator = NoControlCharactersValidator()
        value_with_new_line = "test\nvalue"

        with self.assertRaises(ValidationError) as cm:
            self.validator(value_with_new_line)

        self.assertEqual(
            cm.exception.message,
            "Control Characters like new lines or tabs are not allowed.",
        )
        self.assertEqual(cm.exception.code, "no_control_characters")
        self.assertDictEqual(
            cm.exception.params, {"value": value_with_new_line, "whitelist": None}
        )

    def test_should_raise_custom_message_and_code_if_value_contains_tabs(self):
        self.validator = NoControlCharactersValidator(
            message="custom message", code="custom code"
        )
        value_with_tabs = "test\tvalue"

        with self.assertRaises(ValidationError) as cm:
            self.validator(value_with_tabs)

        self.assertEqual(cm.exception.message, "custom message")
        self.assertEqual(cm.exception.code, "custom code")
        self.assertDictEqual(
            cm.exception.params, {"value": value_with_tabs, "whitelist": None}
        )

    def test_should_not_raise_if_value_contains_characters_which_is_on_whitelist(self):
        self.validator = NoControlCharactersValidator(
            message="custom message", code="custom code", whitelist=["\n"]
        )
        value_with_new_line = "test\nvalue"

        result = self.validator(value_with_new_line)

        self.assertIsNone(result)


class NoWhiteSpaceValidatorTests(TestCase):
    """Tests for NoWhitespaceValidator."""

    def test_should_raise_default_message_and_code_if_value_has_leading_whitespace(
        self,
    ):
        self.validator = NoWhitespaceValidator()

        value_with_leading_whitespace = " test_value"

        with self.assertRaises(ValidationError) as cm:
            self.validator(value_with_leading_whitespace)

        self.assertEqual(
            cm.exception.message, "Leading and Trailing whitespaces are not allowed."
        )
        self.assertEqual(cm.exception.code, "no_whitespace")
        self.assertDictEqual(
            cm.exception.params, {"value": value_with_leading_whitespace}
        )

    def test_should_raise_custom_message_and_code_if_value_has_trailing_whitespace(
        self,
    ):
        self.validator = NoWhitespaceValidator(
            message="custom message", code="custom code"
        )
        value_with_trailing_whitespace = "test value "

        with self.assertRaises(ValidationError) as cm:
            self.validator(value_with_trailing_whitespace)

        self.assertEqual(cm.exception.message, "custom message")
        self.assertEqual(cm.exception.code, "custom code")
        self.assertDictEqual(
            cm.exception.params, {"value": value_with_trailing_whitespace}
        )

    def test_should_not_raise_if_value_doesnt_have_leading_or_trailing_whitespaces(
        self,
    ):
        self.validator = NoWhitespaceValidator()
        value_without_leading_or_trailing_whitespaces = "test value"

        result = self.validator(value_without_leading_or_trailing_whitespaces)

        self.assertIsNone(result)


class TestHexValidator(SimpleTestCase):
    def test_custom_message_and_code(self):
        self.validator = HexValidator(message="message", code="code")

        self.assertEqual(self.validator.message, "message")
        self.assertEqual(self.validator.code, "code")

    def test_equality_of_objs_with_obj_of_different_type(self):
        self.assertNotEqual(TypeError(), HexValidator())

    def test_equality_of_objs_with_different_code(self):
        self.assertNotEqual(HexValidator(code="1"), HexValidator(code="a"))

    def test_equality_of_objs_with_different_message(self):
        self.assertNotEqual(
            HexValidator(code="code", message="a"),
            HexValidator(code="code", message="acb"),
        )

    def test_equality_of_objs_with_same_code_and_message(self):
        self.assertEqual(
            HexValidator(code="c", message="m"), HexValidator(code="c", message="m")
        )

    def test_fixed_length(self):
        value = "abcd"
        self.validator = HexValidator(length=5)

        with self.assertRaises(ValidationError) as err:
            self.validator(value)

        self.assertEqual(
            str(err.exception), "['Invalid length. Must be 5 characters.']"
        )
        self.assertEqual(err.exception.code, "hex_only_length")

    def test_min_length(self):
        value = "a"
        self.validator = HexValidator(min_length=5)

        with self.assertRaises(ValidationError) as err:
            self.validator(value)

        self.assertEqual(
            str(err.exception), "['Ensure that there are more than 5 characters.']"
        )
        self.assertEqual(err.exception.code, "hex_only_min_length")

    def test_with_max_length(self):
        value = "abcd"
        self.validator = HexValidator(max_length=2)

        with self.assertRaises(ValidationError) as err:
            self.validator(value)

        self.assertEqual(
            str(err.exception), "['Ensure that there are no more than 2 characters.']"
        )
        self.assertEqual(err.exception.code, "hex_only_max_length")

    def test_invalid_type(self):
        value = 1
        with patch("django_extensions.validators.force_str", return_value=1):
            self.validator = HexValidator()

            with self.assertRaises(ValidationError) as err:
                self.validator(value)

        self.assertEqual(str(err.exception), "['Only a hex string is allowed.']")
        self.assertEqual(err.exception.code, "hex_only")

    def test_invalid_hex(self):
        value = "1"
        self.validator = HexValidator()

        with self.assertRaises(ValidationError) as err:
            self.validator(value)

        self.assertEqual(str(err.exception), "['Only a hex string is allowed.']")
        self.assertEqual(err.exception.code, "hex_only")

    def test_valid_hex(self):
        value = "b901ef"
        self.validator = HexValidator()

        result = self.validator(value)

        self.assertIsNone(result)
