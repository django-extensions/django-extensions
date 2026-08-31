import json
import os
import tempfile
from contextlib import contextmanager
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


def assert_looks_like_app_dotfile(output: str) -> None:
    assert output.startswith("digraph app_import_dependencies {\n")
    assert output.endswith("}\n")
    assert '"' in output


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


class GraphAppImportDependenciesOutputTests(TestCase):
    def test_requires_app_or_all_applications(self):
        with self.assertRaises(CommandError):
            call_command("graph_app_import_dependencies")

    def test_all_applications_no_output_options_defaults_to_dot(self):
        stdout = StringIO()
        call_command(
            "graph_app_import_dependencies",
            all_applications=True,
            stdout=stdout,
        )
        assert_looks_like_app_dotfile(stdout.getvalue())

    def test_dot_option_to_stdout(self):
        stdout = StringIO()
        call_command(
            "graph_app_import_dependencies",
            all_applications=True,
            dot=True,
            stdout=stdout,
        )
        assert_looks_like_app_dotfile(stdout.getvalue())

    def test_dot_option_to_file(self):
        stdout = StringIO()
        with temp_output_file(".dot") as tmpfname:
            call_command(
                "graph_app_import_dependencies",
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
        out = StringIO()
        call_command(
            "graph_app_import_dependencies",
            all_applications=True,
            json=True,
            stdout=out,
        )
        assert_looks_like_app_jsonfile(out.getvalue())

    def test_json_option_to_file(self):
        stdout = StringIO()
        with temp_output_file(".json") as tmpfname:
            call_command(
                "graph_app_import_dependencies",
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
        with self.assertRaises(CommandError):
            call_command(
                "graph_app_import_dependencies",
                all_applications=True,
                pydot=True,
            )

    def test_pygraphviz_without_file(self):
        with self.assertRaises(CommandError):
            call_command(
                "graph_app_import_dependencies",
                all_applications=True,
                pygraphviz=True,
            )

    def test_rankdir_not_supported_for_json(self):
        with self.assertRaises(CommandError):
            call_command(
                "graph_app_import_dependencies",
                all_applications=True,
                json=True,
                rankdir="LR",
            )

    def test_ordering_not_supported_for_json(self):
        with self.assertRaises(CommandError):
            call_command(
                "graph_app_import_dependencies",
                all_applications=True,
                json=True,
                ordering="in",
            )

    def test_unknown_app_label_raises_command_error(self):
        with self.assertRaises(CommandError):
            call_command("graph_app_import_dependencies", "not_a_real_app", json=True)


class GraphAppImportDependenciesFilteringTests(TestCase):
    def test_positional_app_labels_restrict_to_only_those_apps(self):
        # Selecting a single app label ("only" semantics): edges to apps
        # outside the selection are dropped, not just hidden.
        out = StringIO()
        call_command(
            "graph_app_import_dependencies",
            "graphdeps_cycle_a",
            json=True,
            stdout=out,
        )
        data = json.loads(out.getvalue())
        assert data["apps"] == ["graphdeps_cycle_a"]
        assert data["edges"] == []

    def test_exclude_drops_app_and_its_edges(self):
        out = StringIO()
        call_command(
            "graph_app_import_dependencies",
            "graphdeps_cycle_a",
            "graphdeps_cycle_b",
            exclude="graphdeps_cycle_b",
            json=True,
            stdout=out,
        )
        data = json.loads(out.getvalue())
        assert data["apps"] == ["graphdeps_cycle_a"]
        assert data["edges"] == []

    def test_exclude_external_keeps_local_apps_only(self):
        out = StringIO()
        call_command(
            "graph_app_import_dependencies",
            all_applications=True,
            exclude_external=True,
            json=True,
            stdout=out,
        )
        data = json.loads(out.getvalue())
        # django_extensions is installed in editable mode in this dev
        # environment, so it counts as "local"; django.contrib.auth is an
        # ordinary (non-editable) dependency and must be dropped.
        assert "django_extensions" in data["apps"]
        assert "auth" not in data["apps"]

    def test_exclude_name_prefix_drops_matching_subtree(self):
        out = StringIO()
        call_command(
            "graph_app_import_dependencies",
            "graphdeps_cycle_a",
            "graphdeps_cycle_b",
            exclude_name_prefix="tests.graphdeps_cycle_b",
            json=True,
            stdout=out,
        )
        data = json.loads(out.getvalue())
        assert data["apps"] == ["graphdeps_cycle_a"]

    def test_exclude_file_pattern_drops_matching_edges_only(self):
        # tests/graphdeps_cycle_a/tests.py is the only file in that app
        # importing django_extensions. "test*.py" is passed explicitly
        # here -- it's an example pattern, not a built-in assumption.
        out = StringIO()
        call_command(
            "graph_app_import_dependencies",
            "graphdeps_cycle_a",
            "graphdeps_cycle_b",
            "django_extensions",
            json=True,
            stdout=out,
        )
        edges_with = {(e["from"], e["to"]) for e in json.loads(out.getvalue())["edges"]}
        assert ("graphdeps_cycle_a", "django_extensions") in edges_with

        out = StringIO()
        call_command(
            "graph_app_import_dependencies",
            "graphdeps_cycle_a",
            "graphdeps_cycle_b",
            "django_extensions",
            exclude_file_pattern="test*.py",
            json=True,
            stdout=out,
        )
        edges_without = {
            (e["from"], e["to"]) for e in json.loads(out.getvalue())["edges"]
        }
        assert ("graphdeps_cycle_a", "django_extensions") not in edges_without
        # The non-test edge between the two cycle apps survives -- only
        # files matching the given pattern(s) are dropped.
        assert ("graphdeps_cycle_a", "graphdeps_cycle_b") in edges_without

    def test_exclude_file_pattern_accepts_arbitrary_globs(self):
        # Not specific to tests: an unrelated pattern with a path segment
        # works the same way, matched against the path relative to the app.
        out = StringIO()
        call_command(
            "graph_app_import_dependencies",
            "graphdeps_cycle_a",
            "auth",
            exclude_file_pattern="nested/*.py",
            json=True,
            stdout=out,
        )
        edges = {(e["from"], e["to"]) for e in json.loads(out.getvalue())["edges"]}
        assert ("graphdeps_cycle_a", "auth") not in edges


class GraphAppImportDependenciesCycleTests(TestCase):
    """
    tests.graphdeps_cycle_a and tests.graphdeps_cycle_b import each other
    (see their services.py) -- a real, intentional two-app import cycle
    used to exercise --highlight-cycles end to end.
    """

    def test_cycle_edges_exist_without_highlight_cycles(self):
        out = StringIO()
        call_command(
            "graph_app_import_dependencies",
            "graphdeps_cycle_a",
            "graphdeps_cycle_b",
            json=True,
            stdout=out,
        )
        data = json.loads(out.getvalue())
        assert sorted(data["apps"]) == ["graphdeps_cycle_a", "graphdeps_cycle_b"]
        edge_pairs = {(e["from"], e["to"]) for e in data["edges"]}
        assert edge_pairs == {
            ("graphdeps_cycle_a", "graphdeps_cycle_b"),
            ("graphdeps_cycle_b", "graphdeps_cycle_a"),
        }
        # Off by default: no cycle-report keys at all.
        assert "cycle_groups" not in data
        assert "feedback_edges" not in data

    def test_highlight_cycles_json_reports_group_and_feedback_edge(self):
        out = StringIO()
        call_command(
            "graph_app_import_dependencies",
            "graphdeps_cycle_a",
            "graphdeps_cycle_b",
            json=True,
            highlight_cycles=True,
            stdout=out,
        )
        data = json.loads(out.getvalue())
        assert data["cycle_groups"] == [["graphdeps_cycle_a", "graphdeps_cycle_b"]]
        assert len(data["feedback_edges"]) == 1
        edge = data["feedback_edges"][0]
        assert {edge["from"], edge["to"]} == {
            "graphdeps_cycle_a",
            "graphdeps_cycle_b",
        }

    def test_highlight_cycles_dot_boxes_group_and_reddens_feedback_edge(self):
        stdout = StringIO()
        call_command(
            "graph_app_import_dependencies",
            "graphdeps_cycle_a",
            "graphdeps_cycle_b",
            dot=True,
            highlight_cycles=True,
            stdout=stdout,
        )
        output = stdout.getvalue()
        assert_looks_like_app_dotfile(output)
        assert "subgraph cluster_0 {" in output
        assert 'label="cycle group 1";' in output
        assert output.count("color=red") == 1

    def test_plain_dot_has_no_cluster_or_red_edge(self):
        stdout = StringIO()
        call_command(
            "graph_app_import_dependencies",
            "graphdeps_cycle_a",
            "graphdeps_cycle_b",
            dot=True,
            stdout=stdout,
        )
        output = stdout.getvalue()
        assert "cluster_" not in output
        assert "color=red" not in output
