# coding=utf-8
try:
    from django.apps import AppConfig

    class TestAppConfig(AppConfig):
        name = 'tests.testapp'

except ImportError:
    pass
