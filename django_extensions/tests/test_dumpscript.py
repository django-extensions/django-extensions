import sys
from StringIO import StringIO
from django.test import TestCase
from django.core.management import call_command
from django_extensions.tests.models import Name

class DumpScriptTests(TestCase):
    def setUp(self):
        self.real_stdout = sys.stdout
        sys.stdout = StringIO()

    def tearDown(self):
        sys.stdout = self.real_stdout

    def test_runs(self):
        # lame test...does it run?
        n = Name(name='Gabriel')
        n.save()
        call_command('dumpscript', 'tests')
        self.assertTrue('Gabriel' in sys.stdout.getvalue())
