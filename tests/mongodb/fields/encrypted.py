# -*- coding: utf-8 -*-
import pytest
from django.test import TestCase

from django.conf import settings
from tests.testapp.models import EncryptedFieldsNoSQLModel


@pytest.mark.skipif(settings.DJANGO_EXTENSIONS_MONGODB_DATABASE_NAME, reason="Test can only run on mongodb")
class EncryptedFieldsNoSQLModelTestCase(TestCase):

    def test_save_to_encrypted_charfield(self):
        secret_message = 'hello'
        encrypted_fields_model_obj = EncryptedFieldsNoSQLModel.objects.create(secret_message=secret_message)
        encrypted_fields_model_obj.reload()
        self.assertEqual(encrypted_fields_model_obj.secret_message, secret_message)

    def test_save_to_encrypted_textfield(self):
        secret_text = 'hello' * 10
        encrypted_fields_model_obj = EncryptedFieldsNoSQLModel.objects.create(secret_text=secret_text)
        encrypted_fields_model_obj.reload()
        self.assertEqual(encrypted_fields_model_obj.secret_text, secret_text)

    def test_data_in_encrypted_textfield(self):
        secret_text = 'hello'
        encrypted_fields_model_obj = EncryptedFieldsNoSQLModel.objects.create(secret_text=secret_text)
        self.assertIsNone(EncryptedFieldsNoSQLModel.objects.filter(secret_text=secret_text).first())
        encrypted_fields_model_obj.reload()
        self.assertEqual(encrypted_fields_model_obj.secret_text, secret_text)
