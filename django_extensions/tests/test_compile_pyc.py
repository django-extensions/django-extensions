import os
import six
import fnmatch
from django.test import TestCase
from django.test.utils import override_settings
from django.core.management import call_command
from django_extensions.management.utils import get_project_root


class CompilePycTests(TestCase):
    def setUp(self):
        self._settings = os.environ.get('DJANGO_SETTINGS_MODULE')
        os.environ['DJANGO_SETTINGS_MODULE'] = 'django_extensions.settings'

    def tearDown(self):
        if self._settings:
            os.environ['DJANGO_SETTINGS_MODULE'] = self._settings

    def _find_pyc(self, path, mask='*.pyc'):
        pyc_glob = []
        for root, dirs, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, mask):
                pyc_glob.append(os.path.join(root, filename))
        return pyc_glob

    @override_settings(CLEAN_PYC_DEPRECATION_WAIT=False, COMPILE_PYC_DEPRECATION_WAIT=False)
    def test_assumes_project_root(self):
        out = six.StringIO()
        call_command('compile_pyc', stdout=out)
        expected = "Assuming '%s' is the project root." % get_project_root()
        output = out.getvalue()
        self.assertIn(expected, output)
        call_command('clean_pyc', stdout=out)

    def test_compiles_pyc_files(self):
        with self.settings(BASE_DIR=get_project_root()):
            call_command('clean_pyc')
        pyc_glob = self._find_pyc(get_project_root())
        self.assertEqual(len(pyc_glob), 0)
        with self.settings(BASE_DIR=get_project_root()):
            call_command('compile_pyc')
        pyc_glob = self._find_pyc(get_project_root())
        self.assertTrue(len(pyc_glob) > 0)
        with self.settings(BASE_DIR=get_project_root()):
            call_command('clean_pyc')

    def test_takes_path(self):
        out = six.StringIO()
        project_root = os.path.join(get_project_root(), 'tests', 'testapp')
        with self.settings(BASE_DIR=get_project_root()):
            call_command('clean_pyc', path=project_root)
        pyc_glob = self._find_pyc(project_root)
        self.assertEqual(len(pyc_glob), 0)
        with self.settings(BASE_DIR=get_project_root()):
            call_command('compile_pyc', verbosity=2, path=project_root, stdout=out)
        expected = ['Compiling %s...' % fn for fn in
                    sorted(self._find_pyc(project_root, mask='*.py'))]
        output = out.getvalue().splitlines()
        self.assertEqual(expected, sorted(output))
        with self.settings(BASE_DIR=get_project_root()):
            call_command('clean_pyc')
