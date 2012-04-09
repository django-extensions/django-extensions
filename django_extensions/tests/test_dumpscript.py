import sys
from StringIO import StringIO
from django.test import TestCase
from django.core.management import call_command
from django_extensions.tests.models import Name

from django.conf import settings
from django.db.models import loading

class DumpScriptTests(TestCase):
    def setUp(self):
        self.real_stdout = sys.stdout
        sys.stdout = StringIO()

        settings.INSTALLED_APPS += ('django_extensions.tests',)
        loading.cache.loaded = False
        call_command('syncdb', verbosity=0)

    def tearDown(self):
        sys.stdout = self.real_stdout
        settings.INSTALLED_APPS.pop()
        loading.cache.loaded = False

    def test_runs(self):
        # lame test...does it run?
        n = Name(name='Gabriel')
        n.save()
        call_command('dumpscript', 'tests')
        self.assertTrue('Gabriel' in sys.stdout.getvalue())
