# coding=utf-8
import os

from django.core.management import call_command

from .conftest import find_pyc

project_root = os.path.join('tests', 'testapp')


def test_compiles_pyc_files(settings):
    settings.BASE_DIR = project_root
    call_command('clean_pyc')
    pyc_glob = find_pyc(project_root)
    assert len(pyc_glob) == 0
    call_command('compile_pyc')
    pyc_glob = find_pyc(project_root)
    assert len(pyc_glob) > 0
    call_command('clean_pyc')


def test_takes_path(settings, capsys):
    settings.BASE_DIR = ''
    call_command('clean_pyc', path=project_root)
    pyc_glob = find_pyc(project_root)
    assert len(pyc_glob) == 0
    call_command('compile_pyc', verbosity=2, path=project_root)
    expected = ['Compiling %s...' % fn for fn in sorted(find_pyc(project_root, mask='*.py'))]
    output = capsys.readouterr()[0].splitlines()
    assert expected == sorted(output)
    call_command('clean_pyc', path=project_root)
