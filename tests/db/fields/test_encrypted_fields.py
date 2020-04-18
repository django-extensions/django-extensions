# -*- coding: utf-8 -*-
from django.test import TestCase

from tests.testapp.models import EncryptedFieldsModel


class EncryptedFieldsModelTestCase(TestCase):

    def test_save_to_encrypted_charfield(self):
        secret_message = 'hello'
        encrypted_fields_model_obj = EncryptedFieldsModel.objects.create(secret_message=secret_message)
        encrypted_fields_model_obj.refresh_from_db()
        self.assertEqual(encrypted_fields_model_obj.secret_message, secret_message)

    def test_save_too_long_string_to_encrypted_charfield(self):
        secret_message = 'hello' * 10
        encrypted_fields_model_obj = EncryptedFieldsModel.objects.create(secret_message=secret_message)
        encrypted_fields_model_obj.refresh_from_db()
        self.assertNotEqual(encrypted_fields_model_obj.secret_message, secret_message)
        self.assertEqual(encrypted_fields_model_obj.secret_message, 'hellohello')  # truncated

    def test_save_to_encrypted_textfield(self):
        secret_text = 'hello' * 10
        encrypted_fields_model_obj = EncryptedFieldsModel.objects.create(secret_text=secret_text)
        encrypted_fields_model_obj.refresh_from_db()
        self.assertEqual(encrypted_fields_model_obj.secret_text, secret_text)

    def test_data_in_encrypted_textfield(self):
        secret_text = 'hello'
        encrypted_fields_model_obj = EncryptedFieldsModel.objects.create(secret_text=secret_text)
        self.assertFalse(EncryptedFieldsModel.objects.filter(secret_text=secret_text).exists())  # can't find by string
        encrypted_fields_model_obj.refresh_from_db()
        self.assertEqual(encrypted_fields_model_obj.secret_text, secret_text)
