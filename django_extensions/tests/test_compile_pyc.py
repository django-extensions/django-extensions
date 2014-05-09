import fnmatch
import os
from unittest import TestCase
import six
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

    def test_assumes_project_root(self):
        out = six.StringIO()
        call_command('compile_pyc', stdout=out)
        expected = ('No path specified, assuming %s is the project root.'
                    % get_project_root())
        output = out.getvalue().splitlines()[0]
        self.assertEqual(expected, output)
        call_command('clean_pyc')

    def test_compiles_pyc_files(self):
        call_command('clean_pyc')
        pyc_glob = self._find_pyc(get_project_root())
        self.assertEqual(len(pyc_glob), 0)
        call_command('compile_pyc')
        pyc_glob = self._find_pyc(get_project_root())
        self.assertTrue(len(pyc_glob) > 0)
        call_command('clean_pyc')

    def test_takes_path(self):
        out = six.StringIO()
        project_root = os.path.join(get_project_root(), 'tests', 'testapp')
        call_command('clean_pyc', path=project_root)
        pyc_glob = self._find_pyc(project_root)
        self.assertEqual(len(pyc_glob), 0)
        call_command('compile_pyc', verbosity=2, path=project_root, stdout=out)
        expected = ['Compiling %s...' % fn for fn in
                    sorted(self._find_pyc(project_root, mask='*.py'))]
        output = out.getvalue().splitlines()
        self.assertEqual(expected, sorted(output))
        call_command('clean_pyc')
