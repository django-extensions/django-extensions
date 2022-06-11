# -*- coding: utf-8 -*-
import ast
import os
import shutil
import sys

from io import StringIO
from django.core.management import call_command
from django.test import TestCase, override_settings

from .testapp.models import Name, Note, Person, Club


class DumpScriptTests(TestCase):
    def setUp(self):
        sys.stdout = StringIO()
        sys.stderr = StringIO()

    def test_runs(self):
        # lame test...does it run?
        n = Name(name='Gabriel')
        n.save()
        call_command('dumpscript', 'django_extensions')
        self.assertTrue('Gabriel' in sys.stdout.getvalue())

    def test_replaced_stdout(self):
        # check if stdout can be replaced
        sys.stdout = StringIO()
        n = Name(name='Mike')
        n.save()
        tmp_out = StringIO()
        call_command('dumpscript', 'django_extensions', stdout=tmp_out)
        self.assertTrue('Mike' in tmp_out.getvalue())  # script should go to tmp_out
        self.assertEqual(0, len(sys.stdout.getvalue()))  # there should not be any output to sys.stdout
        tmp_out.close()

    def test_replaced_stderr(self):
        # check if stderr can be replaced, without changing stdout
        n = Name(name='Fred')
        n.save()
        tmp_err = StringIO()
        sys.stderr = StringIO()
        call_command('dumpscript', 'django_extensions', stderr=tmp_err)
        self.assertTrue('Fred' in sys.stdout.getvalue())  # script should still go to stdout
        self.assertTrue('Name' in tmp_err.getvalue())  # error output should go to tmp_err
        self.assertEqual(0, len(sys.stderr.getvalue()))  # there should not be any output to sys.stderr
        tmp_err.close()

    def test_valid_syntax(self):
        n1 = Name(name='John')
        n1.save()
        p1 = Person(name=n1, age=40)
        p1.save()
        n2 = Name(name='Jane')
        n2.save()
        p2 = Person(name=n2, age=18)
        p2.save()
        p2.children.add(p1)
        note1 = Note(note="This is the first note.")
        note1.save()
        note2 = Note(note="This is the second note.")
        note2.save()
        p2.notes.add(note1, note2)
        tmp_out = StringIO()
        call_command('dumpscript', 'django_extensions', stdout=tmp_out)
        ast_syntax_tree = ast.parse(tmp_out.getvalue())
        if hasattr(ast_syntax_tree, 'body'):
            self.assertTrue(len(ast_syntax_tree.body) > 1)
        else:
            self.assertTrue(len(ast_syntax_tree.asList()) > 1)
        tmp_out.close()

    @override_settings(TIME_ZONE='Asia/Seoul')
    def test_with_datetimefield(self):
        django = Club.objects.create(name='Club Django')
        Note.objects.create(
            note='Django Tips',
            club=django,
        )

        dumpscript_path = './django_extensions/scripts'

        os.mkdir(dumpscript_path)
        open(dumpscript_path + '/__init__.py', 'w').close()  # for python 2.7

        # This script will have a dateutil codes.
        # e.g. importer.locate_object(...,
        # 'date_joined': dateutil.parser.parse("2019-05-20T03:32:27.144586+09:00")
        with open(dumpscript_path + '/test.py', 'wt') as test:
            call_command('dumpscript', 'django_extensions', stdout=test)

        # Check dumpscript without exception
        call_command('runscript', 'test')

        # Delete dumpscript
        shutil.rmtree(dumpscript_path)

        # Check if Note is duplicated
        self.assertEqual(Note.objects.filter(note='Django Tips').count(), 2)
