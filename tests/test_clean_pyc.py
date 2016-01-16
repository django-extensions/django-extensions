# coding=utf-8
import os
import shutil

from django.core.management import call_command

from .conftest import find_pyc

project_root = os.path.join('tests', 'testapp')


def test_removes_pyc_files(settings):
    settings.BASE_DIR = project_root
    call_command('compile_pyc')
    pyc_glob = find_pyc(project_root)
    assert len(pyc_glob) > 0
    call_command('clean_pyc')
    pyc_glob = find_pyc(project_root)
    assert len(pyc_glob) == 0


def test_takes_path(capsys):
    call_command('compile_pyc', path=project_root)
    pyc_glob = find_pyc(project_root)
    assert len(pyc_glob) > 0
    call_command('clean_pyc', verbosity=2, path=project_root)
    output = capsys.readouterr()[0].splitlines()
    assert sorted(pyc_glob) == sorted(output)


def test_removes_pyo_files(capsys):
    call_command('compile_pyc', path=project_root)
    pyc_glob = find_pyc(project_root)
    assert len(pyc_glob) > 0
    # Create some fake .pyo files since we can't force them to be created.
    pyo_glob = []
    for fn in pyc_glob:
        pyo = '%s.pyo' % os.path.splitext(fn)[0]
        shutil.copyfile(fn, pyo)
        pyo_glob.append(pyo)
    call_command('clean_pyc', verbosity=2, path=project_root, optimize=True)
    output = capsys.readouterr()[0].splitlines()
    assert sorted(pyc_glob + pyo_glob) == sorted(output)
