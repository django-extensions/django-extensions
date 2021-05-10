import datetime
from django.test import TestCase

from django_extensions.db.fields.crypto_field import (
    CryptoTextField,
)
from tests.testapp.models import (
    CryptoTextModel,
    CryptoTextModelPassword,
    CryptoAllFieldModel,
)


class CryptoFieldTest(TestCase):
    def test_char_field_create(self):
        t = CryptoTextModel.objects.create(text_field="RandomTextField123!")
        self.assertEqual(t.text_field, "RandomTextField123!")

    def test_all_field_create(self):
        text_field = "RandomTextField123!"
        char_field = "RandomCharField123!"
        email_field = "random@email.com"
        int_field = -123
        date_field = datetime.date(2001, 1, 1)
        date_time_field = datetime.datetime(2001, 1, 1, 13, 00)
        big_int_field = -9223372036854775808
        positive_int_field = 123
        positive_small_int_field = 1
        small_int_field = -1

        t = CryptoAllFieldModel.objects.create(
            text_field=text_field,
            char_field=char_field,
            email_field=email_field,
            int_field=int_field,
            date_field=date_field,
            date_time_field=date_time_field,
            big_int_field=big_int_field,
            positive_int_field=positive_int_field,
            positive_small_int_field=positive_small_int_field,
            small_int_field=small_int_field,
        )

        self.assertEqual(t.text_field, text_field)
        self.assertEqual(t.char_field, char_field)
        self.assertEqual(t.email_field, email_field)
        self.assertEqual(t.int_field, int_field)
        self.assertEqual(t.date_field, date_field)
        self.assertEqual(t.date_time_field, date_time_field)
        self.assertEqual(t.big_int_field, big_int_field)
        self.assertEqual(t.positive_int_field, positive_int_field)
        self.assertEqual(t.positive_small_int_field, positive_small_int_field)
        self.assertEqual(t.small_int_field, small_int_field)

    def test_char_field_create_password(self):
        t = CryptoTextModelPassword.objects.create(text_field="RandomTextField123!")
        self.assertEqual(t.text_field, "RandomTextField123!")

    def test_mutable(self):
        t1 = CryptoTextModel.objects.create(text_field="RandomTextField123!")
        t2 = CryptoTextModel.objects.create(text_field="RandomTextField123!")
        self.assertIs(t1.text_field, t2.text_field)

    def test_get_prep_value(self):
        c_text = CryptoTextField()

        self.assertEqual(
            "RandomTextField123!",
            c_text.get_prep_value(value="RandomTextField123!"),
        )

    def test_get_db_prep_save(self):
        c_text = CryptoTextField()
        self.assertIs(
            bytes,
            type(c_text.get_db_prep_save(value="RandomTextField123!", connection=None)),
        )

    def test_to_python(self):
        c_text = CryptoTextField()
        self.assertEqual(str(""), c_text.to_python(""))
        self.assertEqual(str("a"), c_text.to_python("a"))

    def test_password_salt(self):
        c_text = CryptoTextField()
        c2_text = CryptoTextField(password="password_to_be_used_as_key")
        self.assertEqual("Password123!!!", c_text.password)
        self.assertEqual("Salt123!!!", c_text.salt)
        self.assertEqual("password_to_be_used_as_key", c2_text.password)
