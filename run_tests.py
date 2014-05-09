#!/usr/bin/env python

import sys
import shutil
import tempfile

try:
    import django
except ImportError:
    print("Error: missing test dependency:")
    print("  django library is needed to run test suite")
    print("  you can install it with 'pip install django'")
    print("  or use tox to automatically handle test dependencies")
    sys.exit(1)

try:
    import shortuuid
except ImportError:
    print("Error: missing test dependency:")
    print("  shortuuid library is needed to run test suite")
    print("  you can install it with 'pip install shortuuid'")
    print("  or use tox to automatically handle test dependencies")
    sys.exit(1)

try:
    import dateutil
except ImportError:
    print("Error: missing test dependency:")
    print("  dateutil library is needed to run test suite")
    print("  you can install it with 'pip install python-dateutil'")
    print("  or use tox to automatically handle test dependencies")
    sys.exit(1)

try:
    import six
except ImportError:
    print("Error: missing test dependency:")
    print("  six library is needed to run test suite")
    print("  you can install it with 'pip install six'")
    print("  or use tox to automatically handle test dependencies")
    sys.exit(1)

__test_libs__ = [
    django,
    shortuuid,
    dateutil,
    six
]

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
                'django_extensions.tests.testapp',
                'django_extensions',
            ],
            # Django replaces this, but it still wants it. *shrugs*
            DATABASE_ENGINE='django.db.backends.sqlite3',
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            MEDIA_ROOT='/tmp/django_extensions_test_media/',
            MEDIA_PATH='/media/',
            ROOT_URLCONF='django_extensions.tests.urls',
            DEBUG=True,
            TEMPLATE_DEBUG=True,
            ENCRYPTED_FIELD_KEYS_DIR=KEY_LOCS,
        )

        if django.VERSION[:2] >= (1, 7):
            django.setup()

        apps = ['django_extensions']
        if django.VERSION[:2] >= (1, 6):
            apps.append('django_extensions.tests.testapp')
            apps.append('django_extensions.tests')

        from django.core.management import call_command
        from django.test.utils import get_runner

        try:
            from django.contrib.auth import get_user_model
        except ImportError:
            USERNAME_FIELD = "username"
        else:
            USERNAME_FIELD = get_user_model().USERNAME_FIELD

        DjangoTestRunner = get_runner(settings)

        class TestRunner(DjangoTestRunner):
            def setup_databases(self, *args, **kwargs):
                result = super(TestRunner, self).setup_databases(*args, **kwargs)
                kwargs = {
                    "interactive": False,
                    "email": "admin@doesnotexit.com",
                    USERNAME_FIELD: "admin",
                }
                call_command("createsuperuser", **kwargs)
                return result

        failures = TestRunner(verbosity=2, interactive=True).run_tests(apps)
        sys.exit(failures)

    finally:
        for name, path in KEY_LOCS.items():
            # cleanup crypto key temp dirs
            shutil.rmtree(path)


if __name__ == '__main__':
    main()
