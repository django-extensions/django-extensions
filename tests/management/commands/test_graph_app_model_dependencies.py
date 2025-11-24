import json
import os
import tempfile
from contextlib import contextmanager
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


def assert_looks_like_app_dotfile(output: str) -> None:
    assert output.startswith("digraph app_dependencies {\n")
    assert output.endswith("}\n")
    assert '"' in output
    assert "->" in output or ";" in output


def assert_looks_like_app_jsonfile(output: str) -> None:
    data = json.loads(output)
    assert isinstance(data, dict)
    assert "apps" in data
    assert "edges" in data
    assert isinstance(data["apps"], list)
    assert isinstance(data["edges"], list)
    if data["edges"]:
        edge = data["edges"][0]
        assert "from" in edge and "to" in edge
        assert edge["from"] in data["apps"]
        assert edge["to"] in data["apps"]


@contextmanager
def temp_output_file(extension: str = ""):
    """Create writable tempfile in filesystem and ensure it gets deleted"""
    tmpfile = tempfile.NamedTemporaryFile(suffix=extension, delete=False)
    tmpfile.close()
    try:
        yield tmpfile.name
    finally:
        os.unlink(tmpfile.name)


class GraphAppDependenciesOutputTests(TestCase):
    def test_requires_app_or_all_applications(self):
        # Calling without app labels and without --all-applications should fail
        with self.assertRaises(CommandError):
            call_command("graph_app_model_dependencies")

    def test_all_applications_no_output_options_defaults_to_dot(self):
        # Given no output-related options, default to output DOT to stdout
        stdout = StringIO()
        call_command(
            "graph_app_model_dependencies",
            all_applications=True,
            stdout=stdout,
        )
        assert_looks_like_app_dotfile(stdout.getvalue())

    def test_dot_option_to_stdout(self):
        # --dot set but --output not set
        stdout = StringIO()
        call_command(
            "graph_app_model_dependencies",
            all_applications=True,
            dot=True,
            stdout=stdout,
        )
        assert_looks_like_app_dotfile(stdout.getvalue())

    def test_dot_option_to_file(self):
        # --dot set and --output set
        stdout = StringIO()
        with temp_output_file(".dot") as tmpfname:
            call_command(
                "graph_app_model_dependencies",
                all_applications=True,
                dot=True,
                output=tmpfname,
                stdout=stdout,
            )
            with open(tmpfname, "r") as outfile:
                foutput = outfile.read()
        assert_looks_like_app_dotfile(foutput)
        # No output to stdout if writing to file
        assert stdout.getvalue() == ""

    def test_dot_extension_to_file_without_dot_option(self):
        # --dot not set and --output set with .dot extension
        stdout = StringIO()
        with temp_output_file(".dot") as tmpfname:
            call_command(
                "graph_app_model_dependencies",
                all_applications=True,
                output=tmpfname,
                stdout=stdout,
            )
            with open(tmpfname, "r") as outfile:
                foutput = outfile.read()
        assert_looks_like_app_dotfile(foutput)
        assert stdout.getvalue() == ""

    def test_dot_option_trumps_json_extension(self):
        # --dot set and --output set to filename ending with .json
        # assert that --dot option trumps .json file extension
        stdout = StringIO()
        with temp_output_file(".json") as tmpfname:
            call_command(
                "graph_app_model_dependencies",
                all_applications=True,
                dot=True,
                output=tmpfname,
                stdout=stdout,
            )
            with open(tmpfname, "r") as outfile:
                foutput = outfile.read()
        assert_looks_like_app_dotfile(foutput)
        assert stdout.getvalue() == ""

    def test_json_option_to_stdout(self):
        # --json set but --output not set
        out = StringIO()
        call_command(
            "graph_app_model_dependencies",
            all_applications=True,
            json=True,
            stdout=out,
        )
        output = out.getvalue()
        assert_looks_like_app_jsonfile(output)

    def test_json_option_to_file(self):
        # --json set and --output set
        stdout = StringIO()
        with temp_output_file(".json") as tmpfname:
            call_command(
                "graph_app_model_dependencies",
                all_applications=True,
                json=True,
                output=tmpfname,
                stdout=stdout,
            )
            with open(tmpfname, "r") as outfile:
                foutput = outfile.read()
        assert_looks_like_app_jsonfile(foutput)
        assert stdout.getvalue() == ""

    def test_pydot_without_file(self):
        # use of --pydot requires specifying output file
        with self.assertRaises(CommandError):
            call_command(
                "graph_app_model_dependencies",
                all_applications=True,
                pydot=True,
            )

    def test_pygraphviz_without_file(self):
        # use of --pygraphviz requires specifying output file
        with self.assertRaises(CommandError):
            call_command(
                "graph_app_model_dependencies",
                all_applications=True,
                pygraphviz=True,
            )

    def test_rankdir_not_supported_for_json(self):
        # rankdir != TB is not allowed for json output
        with self.assertRaises(CommandError):
            call_command(
                "graph_app_model_dependencies",
                all_applications=True,
                json=True,
                rankdir="LR",
            )

    def test_ordering_not_supported_for_json(self):
        # ordering is not allowed for json output
        with self.assertRaises(CommandError):
            call_command(
                "graph_app_model_dependencies",
                all_applications=True,
                json=True,
                ordering="in",
            )

    def test_limit_to_single_app_label(self):
        # When specifying a single app label, it must be present in JSON apps list
        out = StringIO()
        call_command(
            "graph_app_model_dependencies",
            "django_extensions",
            json=True,
            stdout=out,
        )
        data = json.loads(out.getvalue())
        assert "django_extensions" in data["apps"]
