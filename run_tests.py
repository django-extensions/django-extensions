#!/usr/bin/env python

import sys
import shutil
import tempfile
from django.conf import settings


def main():
    # Dynamically configure the Django settings with the minimum necessary to
    # get Django running tests.
    KEY_LOCS = {}
    try:
        try:
            # If KeyCzar is available, set up the environment.
            from keyczar import keyczart, keyinfo

            # Create an RSA private key.
            keys_dir = tempfile.mkdtemp("django_extensions_tests_keyzcar_rsa_dir")
            keyczart.Create(keys_dir, "test", keyinfo.DECRYPT_AND_ENCRYPT, asymmetric=True)
            keyczart.AddKey(keys_dir, "PRIMARY", size=4096)
            KEY_LOCS['DECRYPT_AND_ENCRYPT'] = keys_dir

            # Create an RSA public key.
            pub_dir = tempfile.mkdtemp("django_extensions_tests_keyzcar_pub_dir")
            keyczart.PubKey(keys_dir, pub_dir)
            KEY_LOCS['ENCRYPT'] = pub_dir
        except ImportError:
            pass

        settings.configure(
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.contenttypes',
                'django.contrib.admin',
                'django.contrib.sessions',
                'django_extensions',
                'django_extensions.tests',
            ],
            # Django replaces this, but it still wants it. *shrugs*
            DATABASE_ENGINE='django.db.backends.sqlite3',
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                }
            },
            MEDIA_ROOT='/tmp/django_extensions_test_media/',
            MEDIA_PATH='/media/',
            ROOT_URLCONF='django_extensions.tests.urls',
            DEBUG=True,
            TEMPLATE_DEBUG=True,
            ENCRYPTED_FIELD_KEYS_DIR=KEY_LOCS,
        )

        from django.test.utils import get_runner
        test_runner = get_runner(settings)(verbosity=2, interactive=True)
        failures = test_runner.run_tests(['django_extensions'])
        sys.exit(failures)

    finally:
        for name, path in KEY_LOCS.items():
            # cleanup crypto key temp dirs
            shutil.rmtree(path)


if __name__ == '__main__':
    main()
