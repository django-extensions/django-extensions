from django.conf import settings


def pytest_configure():
    import sys
    import tempfile

    try:
        import django  # NOQA
    except ImportError:
        print("Error: missing test dependency:")
        print("  django library is needed to run test suite")
        print("  you can install it with 'pip install django'")
        print("  or use tox to automatically handle test dependencies")
        sys.exit(1)

    try:
        import shortuuid  # NOQA
    except ImportError:
        print("Error: missing test dependency:")
        print("  shortuuid library is needed to run test suite")
        print("  you can install it with 'pip install shortuuid'")
        print("  or use tox to automatically handle test dependencies")
        sys.exit(1)

    try:
        import dateutil  # NOQA
    except ImportError:
        print("Error: missing test dependency:")
        print("  dateutil library is needed to run test suite")
        print("  you can install it with 'pip install python-dateutil'")
        print("  or use tox to automatically handle test dependencies")
        sys.exit(1)

    try:
        import six  # NOQA
    except ImportError:
        print("Error: missing test dependency:")
        print("  six library is needed to run test suite")
        print("  you can install it with 'pip install six'")
        print("  or use tox to automatically handle test dependencies")
        sys.exit(1)

    # Dynamically configure the Django settings with the minimum necessary to
    # get Django running tests.
    KEY_LOCS = {}
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
            'tests.testapp',
            'django_extensions',
        ],
        MIDDLEWARE_CLASSES=(
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ),
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
        ROOT_URLCONF='tests.urls',
        DEBUG=True,
        TEMPLATE_DEBUG=True,
        ENCRYPTED_FIELD_KEYS_DIR=KEY_LOCS,
    )
