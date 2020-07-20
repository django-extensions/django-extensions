# -*- coding: utf-8 -*-
import json
import os
import re
import tempfile
from contextlib import contextmanager
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


def assert_looks_like_dotfile(output):
    assert output.startswith("digraph model_graph {\n")
    assert output.endswith("}\n")
    assert "// Dotfile by Django-Extensions graph_models\n" in output
    assert "// Labels\n" in output
    assert "// Relations\n" in output


def assert_looks_like_jsonfile(output):
    assert '"created_at": ' in output
    assert '"cli_options": ' in output
    assert '"app_name": "django.contrib.auth"' in output
    assert "created_at" in json.loads(output)


@contextmanager
def temp_output_file(extension=""):
    """Create writable tempfile in filesystem and ensure it gets deleted"""
    tmpfile = tempfile.NamedTemporaryFile(suffix=extension, delete=False)
    tmpfile.close()
    yield tmpfile.name
    os.unlink(tmpfile.name)


class GraphModelsOutputTests(TestCase):
    def test_graph_models_no_output_options(self):
        # Given no output-related options, default to output a Dotfile
        stdout = StringIO()
        call_command('graph_models', all_applications=True, stdout=stdout)
        assert_looks_like_dotfile(stdout.getvalue())

    def test_graph_models_dot_option_to_stdout(self):
        # --dot set but --output not set
        stdout = StringIO()
        call_command('graph_models', all_applications=True, dot=True, stdout=stdout)
        assert_looks_like_dotfile(stdout.getvalue())

    def test_graph_models_dot_option_to_file(self):
        # --dot set and --output set
        stdout = StringIO()
        with temp_output_file(".dot") as tmpfname:
            call_command('graph_models', all_applications=True, dot=True, output=tmpfname, stdout=stdout)
            with open(tmpfname, 'r') as outfile:
                foutput = outfile.read()
        assert_looks_like_dotfile(foutput)
        assert stdout.getvalue() == ""

    def test_graph_models_dot_extensions_to_file(self):
        # --dot not set and --output set
        stdout = StringIO()
        with temp_output_file(".dot") as tmpfname:
            call_command('graph_models', all_applications=True, output=tmpfname, stdout=stdout)
            with open(tmpfname, 'r') as outfile:
                foutput = outfile.read()
        assert_looks_like_dotfile(foutput)
        assert stdout.getvalue() == ""

    def test_graph_models_dot_option_trumps_json_file_extension(self):
        # --dot set and --output set to filename ending with .json
        # assert that --dot option trumps .json file extension
        stdout = StringIO()
        with temp_output_file(".json") as tmpfname:
            call_command('graph_models', all_applications=True, dot=True, output=tmpfname, stdout=stdout)
            with open(tmpfname, 'r') as outfile:
                foutput = outfile.read()
        assert_looks_like_dotfile(foutput)
        assert stdout.getvalue() == ""

    def test_graph_models_json_option_to_stdout(self):
        # --json set but --output not set
        out = StringIO()
        call_command('graph_models', all_applications=True, json=True, stdout=out)
        output = out.getvalue()
        assert_looks_like_jsonfile(output)

    def test_graph_models_json_option_to_file(self):
        # --dot set and --output set
        stdout = StringIO()
        with temp_output_file(".json") as tmpfname:
            call_command('graph_models', all_applications=True, json=True, output=tmpfname, stdout=stdout)
            with open(tmpfname, 'r') as outfile:
                foutput = outfile.read()
        assert_looks_like_jsonfile(foutput)
        assert stdout.getvalue() == ""

    def test_graph_models_pydot_without_file(self):
        # use of --pydot requires specifying output file
        with self.assertRaises(CommandError):
            call_command('graph_models', all_applications=True, pydot=True)

    def test_graph_models_pygraphviz_without_file(self):
        # use of --pygraphviz requires specifying output file
        with self.assertRaises(CommandError):
            call_command('graph_models', all_applications=True, pygraphviz=True)


def test_disable_abstract_fields_not_active():
    out = StringIO()
    call_command(
        'graph_models',
        'django_extensions',
        include_models=['AbstractInheritanceTestModelChild'],
        disable_abstract_fields=False,
        stdout=out,
    )

    output = out.getvalue()
    assert 'my_field_that_my_child_will_inherit' in output


def test_disable_abstract_fields_active():
    out = StringIO()
    call_command(
        'graph_models',
        'django_extensions',
        include_models=['AbstractInheritanceTestModelChild'],
        disable_abstract_fields=True,
        stdout=out,
    )

    output = out.getvalue()
    assert 'my_field_that_my_child_will_inherit' not in output


def test_exclude_models_hides_relationships():
    """ Expose bug #1229 where excluded models appear in relationships.

    They are replaced with an underscore, but the relationship is still there.
    """
    out = StringIO()
    call_command(
        'graph_models',
        'django_extensions',
        exclude_models=['Personality', 'Note'],
        stdout=out,
    )

    output = out.getvalue()
    assert 'tests_testapp_models_Person -> tests_testapp_models_Name' in output
    assert 'tests_testapp_models_Person -> _' not in output


def test_hide_edge_labels():
    out = StringIO()
    call_command('graph_models', 'django_extensions', all_applications=True, hide_edge_labels=True, stdout=out)
    output = out.getvalue()
    assert not re.search(r'\[label=\"[a-zA-Z]+"\]', output)
