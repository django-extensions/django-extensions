from django.test import SimpleTestCase

from django_extensions.management.app_import_graph import (
    AppDependencyGraph,
    build_app_dependency_graph,
)


class CycleGroupsTests(SimpleTestCase):
    def test_no_cycle_gives_no_groups(self):
        graph = AppDependencyGraph(
            edges=frozenset({("a", "b"), ("b", "c")}),
            app_labels=("a", "b", "c"),
        )
        self.assertEqual(graph.cycle_groups(), [])
        self.assertEqual(graph.feedback_edges(), frozenset())

    def test_two_app_cycle_is_one_group(self):
        graph = AppDependencyGraph(
            edges=frozenset({("a", "b"), ("b", "a")}),
            app_labels=("a", "b"),
        )
        self.assertEqual(graph.cycle_groups(), [frozenset({"a", "b"})])

    def test_three_app_cycle_plus_unrelated_edge(self):
        # a -> b -> c -> a is one cycle group; a -> d is not part of it.
        graph = AppDependencyGraph(
            edges=frozenset({("a", "b"), ("b", "c"), ("c", "a"), ("a", "d")}),
            app_labels=("a", "b", "c", "d"),
        )
        self.assertEqual(graph.cycle_groups(), [frozenset({"a", "b", "c"})])

    def test_two_cycles_sharing_an_app_are_one_group(self):
        # a<->b and b<->c share app "b" -- mutually reachable, so this is a
        # single group of three, not two separate groups of two.
        graph = AppDependencyGraph(
            edges=frozenset({("a", "b"), ("b", "a"), ("b", "c"), ("c", "b")}),
            app_labels=("a", "b", "c"),
        )
        self.assertEqual(graph.cycle_groups(), [frozenset({"a", "b", "c"})])

    def test_disjoint_cycles_are_separate_groups(self):
        graph = AppDependencyGraph(
            edges=frozenset({("a", "b"), ("b", "a"), ("c", "d"), ("d", "c")}),
            app_labels=("a", "b", "c", "d"),
        )
        groups = graph.cycle_groups()
        self.assertEqual(len(groups), 2)
        self.assertIn(frozenset({"a", "b"}), groups)
        self.assertIn(frozenset({"c", "d"}), groups)

    def test_self_import_is_its_own_group(self):
        graph = AppDependencyGraph(
            edges=frozenset({("a", "a")}),
            app_labels=("a",),
        )
        self.assertEqual(graph.cycle_groups(), [frozenset({"a"})])

    def test_single_app_with_no_self_import_is_not_a_group(self):
        graph = AppDependencyGraph(edges=frozenset(), app_labels=("a",))
        self.assertEqual(graph.cycle_groups(), [])


class FeedbackEdgesTests(SimpleTestCase):
    def test_two_app_cycle_has_exactly_one_feedback_edge(self):
        edges = frozenset({("a", "b"), ("b", "a")})
        graph = AppDependencyGraph(edges=edges, app_labels=("a", "b"))
        feedback = graph.feedback_edges()
        self.assertEqual(len(feedback), 1)
        self.assertIn(next(iter(feedback)), edges)

    def test_removing_feedback_edges_breaks_every_cycle(self):
        # Every group's induced subgraph, minus its feedback edges, must
        # itself be free of cycles -- that's the actionable guarantee.
        graph = AppDependencyGraph(
            edges=frozenset(
                {("a", "b"), ("b", "c"), ("c", "a"), ("c", "d"), ("d", "c")}
            ),
            app_labels=("a", "b", "c", "d"),
        )
        feedback = graph.feedback_edges()
        remaining = graph.edges - feedback
        remaining_graph = AppDependencyGraph(
            edges=remaining, app_labels=graph.app_labels
        )
        self.assertEqual(remaining_graph.cycle_groups(), [])

    def test_no_cycle_has_no_feedback_edges(self):
        graph = AppDependencyGraph(
            edges=frozenset({("a", "b"), ("b", "c")}), app_labels=("a", "b", "c")
        )
        self.assertEqual(graph.feedback_edges(), frozenset())

    def test_feedback_edge_choice_is_deterministic(self):
        # Regression test: edges and cycle_groups() are built from
        # frozensets, whose iteration order is randomized per Python
        # process (PYTHONHASHSEED) -- without sorting internally, which of
        # the two directions gets reported as "the" feedback edge for a
        # cycle with edges both ways would silently vary from run to run
        # on the exact same graph. Repeat the same call several times as a
        # weak proxy for "not accidentally reading dict/set order".
        edges = frozenset({("alpha", "zeta"), ("zeta", "alpha")})
        results = {
            AppDependencyGraph(
                edges=edges, app_labels=("alpha", "zeta")
            ).feedback_edges()
            for _ in range(20)
        }
        self.assertEqual(results, {frozenset({("zeta", "alpha")})})


class ToDotTests(SimpleTestCase):
    def test_plain_dot_has_no_cluster_or_color(self):
        graph = AppDependencyGraph(
            edges=frozenset({("a", "b"), ("b", "a")}), app_labels=("a", "b")
        )
        dot = graph.to_dot()
        self.assertTrue(dot.startswith("digraph app_import_dependencies {\n"))
        self.assertTrue(dot.endswith("}\n"))
        self.assertNotIn("cluster_", dot)
        self.assertNotIn("color=red", dot)

    def test_highlight_cycles_boxes_group_and_reddens_one_edge(self):
        graph = AppDependencyGraph(
            edges=frozenset({("a", "b"), ("b", "a"), ("a", "c")}),
            app_labels=("a", "b", "c"),
        )
        dot = graph.to_dot(highlight_cycles=True)
        self.assertIn("subgraph cluster_0 {", dot)
        self.assertIn('label="cycle group 1";', dot)
        self.assertEqual(dot.count("color=red"), 1)
        # The non-cycle edge a -> c is untouched.
        self.assertIn('"a" -> "c";', dot)

    def test_highlight_cycles_with_no_cycle_matches_plain_output(self):
        graph = AppDependencyGraph(edges=frozenset({("a", "b")}), app_labels=("a", "b"))
        self.assertEqual(graph.to_dot(), graph.to_dot(highlight_cycles=True))

    def test_rankdir_and_ordering_are_applied(self):
        graph = AppDependencyGraph(edges=frozenset(), app_labels=("a",))
        dot = graph.to_dot(rankdir="LR", ordering="out")
        self.assertIn("rankdir=LR;", dot)
        self.assertIn('graph [ordering="out"];', dot)


class BuildAppDependencyGraphTests(SimpleTestCase):
    def test_only_restricts_nodes_and_drops_dangling_edges(self):
        # django_extensions imports from itself only, and nothing outside
        # the selected set should leak in as a node or edge.
        graph = build_app_dependency_graph(only=frozenset({"django_extensions"}))
        self.assertEqual(graph.app_labels, ("django_extensions",))
        for source, target in graph.edges:
            self.assertEqual(source, "django_extensions")
            self.assertEqual(target, "django_extensions")

    def test_unknown_app_label_raises_value_error(self):
        with self.assertRaises(ValueError):
            build_app_dependency_graph(only=frozenset({"not_a_real_app"}))

    def test_exclude_removes_app_from_result(self):
        graph = build_app_dependency_graph(
            only=frozenset({"django_extensions", "auth"}),
            exclude=frozenset({"auth"}),
        )
        self.assertNotIn("auth", graph.app_labels)

    def test_exclude_external_keeps_editable_installed_app(self):
        # django_extensions is installed with `pip install -e .` in this
        # dev environment, so it resolves to its real source location, not
        # site-packages -- it must survive --exclude-external.
        graph = build_app_dependency_graph(exclude_external=True)
        self.assertIn("django_extensions", graph.app_labels)
        self.assertNotIn("auth", graph.app_labels)

    def test_exclude_name_prefix_drops_matching_subtree(self):
        graph = build_app_dependency_graph(
            only=frozenset({"django_extensions", "auth"}),
            exclude_name_prefixes=frozenset({"django.contrib.auth"}),
        )
        self.assertNotIn("auth", graph.app_labels)
        self.assertIn("django_extensions", graph.app_labels)

    def test_file_pattern_edges_are_included_by_default(self):
        # tests/graphdeps_cycle_a/tests.py is the only file in that app
        # that imports django_extensions.
        graph = build_app_dependency_graph(
            only=frozenset({"graphdeps_cycle_a", "django_extensions"})
        )
        self.assertIn(("graphdeps_cycle_a", "django_extensions"), graph.edges)

    def test_exclude_file_pattern_drops_matching_files_by_name(self):
        # "test*.py" is just an example pattern here, not a built-in
        # assumption -- any glob works, matched against the bare filename.
        graph = build_app_dependency_graph(
            only=frozenset(
                {"graphdeps_cycle_a", "graphdeps_cycle_b", "django_extensions"}
            ),
            exclude_file_patterns=frozenset({"test*.py"}),
        )
        self.assertNotIn(("graphdeps_cycle_a", "django_extensions"), graph.edges)
        # The services.py edge between the two cycle apps is untouched --
        # only files matching the given pattern(s) are dropped.
        self.assertIn(("graphdeps_cycle_a", "graphdeps_cycle_b"), graph.edges)

    def test_exclude_file_pattern_is_not_specific_to_tests(self):
        # An arbitrary, non-"test" pattern works exactly the same way --
        # this drops services.py itself, breaking the cycle entirely.
        graph = build_app_dependency_graph(
            only=frozenset({"graphdeps_cycle_a", "graphdeps_cycle_b"}),
            exclude_file_patterns=frozenset({"services.py"}),
        )
        self.assertEqual(graph.edges, frozenset())

    def test_exclude_file_pattern_matches_relative_path_not_just_basename(self):
        # nested/helper.py is the only file in graphdeps_cycle_a that
        # imports django.contrib.auth. A pattern with a path segment
        # matches against the file's path relative to its app root, not
        # just the bare filename.
        graph = build_app_dependency_graph(
            only=frozenset({"graphdeps_cycle_a", "auth"})
        )
        self.assertIn(("graphdeps_cycle_a", "auth"), graph.edges)

        graph = build_app_dependency_graph(
            only=frozenset({"graphdeps_cycle_a", "auth"}),
            exclude_file_patterns=frozenset({"nested/*.py"}),
        )
        self.assertNotIn(("graphdeps_cycle_a", "auth"), graph.edges)
