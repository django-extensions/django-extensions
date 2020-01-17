# -*- coding: utf-8 -*-
import os
import six
import shutil
from tempfile import mkdtemp

import django
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.forms.widgets import Textarea, TextInput
from django.test import TestCase
from django.test.utils import override_settings

try:
    from django_extensions.db.fields.encrypted import BaseEncryptedField, EncryptedCharField, EncryptedTextField
    keyczar_active = True
except ImportError:
    keyczar_active = False

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch


KEYCZAR_META = '''{"name": "Test", "purpose": "DECRYPT_AND_ENCRYPT", "type": "RSA_PRIV", "encrypted": false, "versions": [{"versionNumber": 1, "status": "PRIMARY", "exportable": false}]}'''  # noqa
KEYCZAR_1 = '''{"publicKey": {"modulus": "AKljEv64fu7jXoyURILoKcYueSXCodwXuvSgjGAV9I9SWUGAKc_0pj2s5xr8eiuhUrcscdSIFD58JwfdWHikI5YhhkxURBa_1DQ3nkMKWVugzuFk5i_8bVOp0Vp-GOAhHEFfyqxhM1yMJrvarCB23scErLVdM99v7ULrL0_Gcwk2jfoFw8pV7shlJ16WL4mM1yFBrE8Eru-iKkhXoo0XiNgk9PMrmys4q_vnWbcw19V0ywY-ks9Q7d0HzNOYmaWLoTUf4RRR72eeVIcrSAgERLsYW6ukk5sr6QGNWLSgft_nahKQazWlqTP4yRV8iTv-GxAn6IJeeiDzFGJV7myxxXs", "publicExponent": "AQAB", "size": 2048}, "privateExponent": "a7VFGdWlWTAZKhkJq5gHIC7i-CDYHYS1a-I_AMZVOWFqwhzF-aceom80kVNkOCQf3bwUMcnJ3aXCh9y26hetTUTKCfU3SqP2QrHvH8AP7BTIGEi5ml_QAPgl2H4AQVysg-FulchFCZ9Q7fjxpL8Rj8moLLc0Ser5GqlD711IPt150IdhfRiK35_ksskBsH-a-695kg-DO8Gf5T1KX0b79y5HumbViwtJJzrxPvGx9_FyhkqKyaIA9h33J1YBHz4VCD20oEGzBC4WnK-gqLselY3Qcdz3_449vI9-3Y7r69VXFopREm6Noz6s53-Cg0kMs62mCiRJYeJGFtiaqaaEsQ", "primeP": "ANfWqgciiwTLyYAEaoYI6E7R82HoWPooEf1GhqKyqhVtd47Ap-FOKi-APAYF7b4NcbV6SJPl6BqjsiDqsdJ3PnjDY_eUbEEkDjmGuYPKT8pRi8XHEOzxm4ARzMIgysTWXtzteyFFeKmhc3cqM6xORqLei1ZwU5mFM4xCrrbcD6fz", "primeQ": "AMjnuGL1JVvKy5rBOOjoe7ia02vtNzUOsdLSUr5NoFODxsIi64UFhzVmA6xvlK_zZeFWoe784_JpXJGKuJ3Bs_kJR2jgVc71Q0Nc8fn0LIFvkrQ6tMZ5XTfLEIHCH8psHA2Q_vR7yRAACZXfY5we2HB9979p6sOsapqgNgWTyJZZ", "primeExponentP": "awt8whMgrV1AbyxBhH4wcL7xnRI15sMuwNVUeqZvcjcbP4JPAI_anjpUCoywLzzNszqVejxg061x759WV9Jp-ky1bJmA4wG1yFQH99PDpMyyrIEg5NKi026AhZrr1ZmX7KwfEA47XK3E7UnR3Nfpcmc65cDJxW7pdNuxeOFFJn8", "primeExponentQ": "XrDgtjuHHSmLJ2iU0ynoTk0jAwZuc-J2K8CX4TwjKdm9T3k3-p1tadyoNJjuwrN8vGWhs0ucgH_qcmqosyo-Ek2uS58Yso_k4RYosr_ETklxIuNcmwNOzWI3aIE_jJ_B5R8HG-JQFOt_mRUOFOJw7yxgHeblEM7t--0xKRXLgBk", "crtCoefficient": "AMr3lac4iHbnKSO4fwyY2WPaIhKM8VWZC3DEkA9Y4uYt8Xe4diw6K_n0e0t_u46fgBcTzj0vNUCiC_i1kcAuLKH2oZUOvAUhoYnjss9LHu9TRI28QEHj6OW0Gghjr4IyW5jg7SYbQngJmnA4QgbMibqFvtKdBSTf-5okujE8QVSb", "size": 2048}'''  # noqa
ENCRYPTED_TEST_VALUE = 'enc_str:::AGFc2bEtqb4ybkQ7kGBBJEnsEPMJAjX5BIIWNKok-g8r2D2WNNt3CbUen2oYr_a5cCN0kvCTfRgBiuaJO04ioB3OuGI-KrQbeJp9GZbs8zc0jTsd7MIgJz6saqmWbZwNDPZYxNBnqdRDxCo1B-nnNrUzYJRb7d0nn_iPwUY4avOLiePCqDX_NRZ7WVooZjzTkRpfpiPvC3gWuKzoz0Cu2AuwdEcO9422BtRDhI30yu7dk5VUL6Zv3OxOz5fvFkJjW-eg3EcGfj2q7_J-YWLVkWsrrwdFJK4w4Yeqkl06qF5sdkakJn2rJJRsSTcDj0ceWAqfnEECdtHkXe0LpfZY1zH_Hwyz'  # noqa


class BaseEncryptedFieldTestCase(TestCase):

    @classmethod
    def setUpClass(cls):  # noqa
        cls.tmpdir = mkdtemp()
        with open(os.path.join(cls.tmpdir, 'meta'), 'w') as f:
            f.write(KEYCZAR_META)
        with open(os.path.join(cls.tmpdir, '1'), 'w') as f:
            f.write(KEYCZAR_1)

    @classmethod
    def tearDownClass(cls):  # noqa
        shutil.rmtree(cls.tmpdir)


@pytest.mark.skipif(keyczar_active is False, reason="Encrypted fields needs that keyczar is installed")
class BaseEncryptionFieldExceptions(TestCase):
    """Tests for BaseEncryptedField exceptions."""

    @override_settings(
        ENCRYPTED_FIELD_KEYS_DIR=None,
        ENCRYPTED_FIELD_MODE='INVALID'
    )
    def test_should_raise_ImproperlyConfigured_if_ENCRYPTED_FIELD_KEYS_DIR_is_not_set(self):  # noqa
        with six.assertRaisesRegex(
                self,
            ImproperlyConfigured,
            'You must set the settings.ENCRYPTED_FIELD_KEYS_DIR setting to your Keyczar keys directory'):  # noqa
            BaseEncryptedField()

    @override_settings(
        ENCRYPTED_FIELD_KEYS_DIR='/srv/keys',
        ENCRYPTED_FIELD_MODE='INVALID'
    )
    def test_should_raise_ImproperlyConfigured_if_invalid_ENCRYPTED_FIELD_MODE_is_set(self):  # noqa
        with six.assertRaisesRegex(
                self,
                ImproperlyConfigured,
                'ENCRYPTED_FIELD_MODE must be either DECRYPT_AND_ENCRYPT or ENCRYPT, not INVALID.'):  # noqa
            BaseEncryptedField()


@pytest.mark.skipif(keyczar_active is False, reason="Encrypted fields needs that keyczar is installed")
class EncryptedCharFieldTests(BaseEncryptedFieldTestCase):

    def test_should_return_formfield_with_TextInput_widget(self):
        with override_settings(ENCRYPTED_FIELD_KEYS_DIR=self.tmpdir):
            formfield = EncryptedCharField(max_length=50).formfield()

        self.assertTrue(isinstance(formfield.widget, TextInput))
        self.assertEqual(formfield.max_length, 358)

    @override_settings(ENCRYPTED_FIELD_MODE='ENCRYPT')
    @patch('django_extensions.db.fields.encrypted.keyczar')
    def test_should_encrypt_foo_and_return_encrypted_value_with_prefix(self, m_keyczar):  # noqa
        m_keyczar.Encrypter.Read.return_value.Encrypt.return_value = 'encrypted_foo'  # noqa
        with override_settings(ENCRYPTED_FIELD_KEYS_DIR=self.tmpdir):
            field = EncryptedCharField(max_length=50)

        result = field.get_db_prep_save('foo', None)

        self.assertTrue(result.startswith('enc_str:::encrypted_foo'))

    @pytest.mark.skipif(django.VERSION < (2, 0), reason='run only on Django greater than 2.0')
    def test_should_decrypt_encrypted_str(self):  # noqa
        with override_settings(ENCRYPTED_FIELD_KEYS_DIR=self.tmpdir):
            field = EncryptedCharField(max_length=50)

        result = field.from_db_value(ENCRYPTED_TEST_VALUE, None, None)

        self.assertEqual(result, 'test')

    @override_settings(ENCRYPTED_FIELD_MODE='ENCRYPT')
    def test_should_return_encrypted_str_if_Decrypt_is_not_available(self):
        with override_settings(ENCRYPTED_FIELD_KEYS_DIR=self.tmpdir):
            field = EncryptedCharField(max_length=50)

        result = field.to_python(ENCRYPTED_TEST_VALUE)

        self.assertEqual(result, ENCRYPTED_TEST_VALUE)

    def test_should_return_encrypted_str_if_value_not_start_with_prefix(self):
        with override_settings(ENCRYPTED_FIELD_KEYS_DIR=self.tmpdir):
            field = EncryptedCharField(max_length=50)

        result = field.to_python('encrypted_value_without_prefix')

        self.assertEqual(result, 'encrypted_value_without_prefix')

    def test_should_return_CharField_as_internal_type(self):
        with override_settings(ENCRYPTED_FIELD_KEYS_DIR=self.tmpdir):
            internal_type = EncryptedCharField(max_length=50).get_internal_type()

        self.assertEqual(internal_type, 'CharField')


@pytest.mark.skipif(keyczar_active is False, reason="Encrypted fields needs that keyczar is installed")
class EncryptedTextFieldTests(BaseEncryptedFieldTestCase):

    def test_should_return_formfield_with_Textarea_widget(self):
        with override_settings(ENCRYPTED_FIELD_KEYS_DIR=self.tmpdir):
            formfield = EncryptedTextField(max_length=50).formfield()

        self.assertTrue(isinstance(formfield.widget, Textarea))

    def test_should_return_TextField_as_internal_type(self):
        with override_settings(ENCRYPTED_FIELD_KEYS_DIR=self.tmpdir):
            internal_type = EncryptedTextField(max_length=50).get_internal_type()

        self.assertEqual(internal_type, 'TextField')
