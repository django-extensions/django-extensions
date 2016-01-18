# coding=utf-8
import ast
import sys

import pytest
import six
from django.core.management import call_command

from .testapp.models import Name, Note, Person

pytestmark = pytest.mark.django_db


def test_runs(capsys):
    # lame test...does it run?
    Name.objects.create(name='Gabriel')
    call_command('dumpscript', 'django_extensions')
    assert 'Gabriel' in capsys.readouterr()[0]


@pytest.mark.usefixtures('capsys')
def test_replaced_stdout():
    Name.objects.create(name='Mike')
    tmp_out = six.StringIO()
    call_command('dumpscript', 'django_extensions', stdout=tmp_out)
    assert 'Mike' in tmp_out.getvalue()  # script should go to tmp_out
    assert 0 == len(sys.stdout.getvalue())  # there should not be any output to sys.stdout
    tmp_out.close()


@pytest.mark.usefixtures('capsys')
def test_replaced_stderr():
    # check if stderr can be replaced, without changing stdout
    Name.objects.create(name='Fred')
    tmp_err = six.StringIO()
    sys.stderr = six.StringIO()
    call_command('dumpscript', 'django_extensions', stderr=tmp_err)
    assert 'Fred' in sys.stdout.getvalue()  # script should still go to stdout
    assert 'Name' in tmp_err.getvalue()  # error output should go to tmp_err
    assert len(sys.stderr.getvalue()) == 0  # there should not be any output to sys.stderr
    tmp_err.close()


def test_valid_syntax():
    n1 = Name.objects.create(name='John')
    p1 = Person.objects.create(name=n1, age=40)
    n2 = Name.objects.create(name='Jane')
    p2 = Person.objects.create(name=n2, age=18)
    p2.children.add(p1)
    note1 = Note.objects.create(note="This is the first note.")
    note2 = Note.objects.create(note="This is the second note.")
    p2.notes.add(note1, note2)
    tmp_out = six.StringIO()
    call_command('dumpscript', 'django_extensions', stdout=tmp_out)
    ast_syntax_tree = ast.parse(tmp_out.getvalue())
    if hasattr(ast_syntax_tree, 'body'):
        assert len(ast_syntax_tree.body) > 1
    else:
        assert len(ast_syntax_tree.asList()) > 1
    tmp_out.close()
