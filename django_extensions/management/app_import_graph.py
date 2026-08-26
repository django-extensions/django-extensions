from __future__ import annotations

import ast
import fnmatch
import importlib.util
import site
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from django.apps import apps

if TYPE_CHECKING:
    from django.apps.config import AppConfig

Edge = tuple[str, str]

_CYCLE_PALETTE = (
    "lightpink",
    "lightblue",
    "lightgoldenrod1",
    "palegreen",
    "plum",
    "lightsalmon",
)


@dataclass(frozen=True)
class AppDependencyGraph:
    """Cross-app import edges, one (source_label, target_label) pair per
    distinct app-to-app dependency actually found in source."""

    edges: frozenset[Edge]
    app_labels: tuple[str, ...]

    def _adjacency(self) -> dict[str, list[str]]:
        # Iterate self.edges (a frozenset, so its natural iteration order
        # depends on Python's per-process hash randomization) in sorted
        # order instead, so that when a cycle has edges in both directions
        # between the same two apps, which one DFS visits first -- and so
        # which one feedback_edges() reports -- is reproducible across runs
        # rather than PYTHONHASHSEED-dependent.
        adjacency: dict[str, list[str]] = {label: [] for label in self.app_labels}
        for source, target in sorted(self.edges):
            adjacency[source].append(target)
        return adjacency

    def cycle_groups(self) -> list[frozenset[str]]:
        """
        Every nontrivial strongly connected component -- apps that are
        mutually reachable from each other, i.e. genuinely on a cycle
        together. Two cycles sharing even one app are the same group here,
        not two: that's what "mutually reachable" means, not a modeling
        choice. A single app with no self-import is never its own group.
        """
        adjacency = self._adjacency()
        sccs = _strongly_connected_components(self.app_labels, adjacency)
        return [
            frozenset(scc)
            for scc in sccs
            if len(scc) > 1 or scc[0] in adjacency[scc[0]]
        ]

    def feedback_edges(self) -> frozenset[Edge]:
        """The specific edges that close each cycle group -- the minimal,
        actionable "cut these" set, not just "these apps are entangled"."""
        adjacency = self._adjacency()
        edges: set[Edge] = set()
        for group in self.cycle_groups():
            edges |= _feedback_edges_within_group(group, adjacency)
        return frozenset(edges)

    def to_dot(
        self,
        *,
        rankdir: str = "TB",
        ordering: str | None = None,
        highlight_cycles: bool = False,
    ) -> str:
        if not highlight_cycles:
            return self._to_dot_plain(rankdir=rankdir, ordering=ordering)
        return self._to_dot_with_cycles(rankdir=rankdir, ordering=ordering)

    def _to_dot_plain(self, *, rankdir: str, ordering: str | None) -> str:
        lines = ["digraph app_import_dependencies {", f"  rankdir={rankdir};"]
        if ordering:
            lines.append(f'  graph [ordering="{ordering}"];')
        lines.extend(f'  "{label}";' for label in self.app_labels)
        lines.extend(
            f'  "{source}" -> "{target}";' for source, target in sorted(self.edges)
        )
        lines.append("}")
        return "\n".join(lines) + "\n"

    def _to_dot_with_cycles(self, *, rankdir: str, ordering: str | None) -> str:
        groups = self.cycle_groups()
        feedback = self.feedback_edges()
        grouped_labels = {label for group in groups for label in group}

        lines = ["digraph app_import_dependencies {", f"  rankdir={rankdir};"]
        if ordering:
            lines.append(f'  graph [ordering="{ordering}"];')
        for i, group in enumerate(groups):
            color = _CYCLE_PALETTE[i % len(_CYCLE_PALETTE)]
            lines.append(f"  subgraph cluster_{i} {{")
            lines.append(f'    label="cycle group {i + 1}";')
            lines.append(f'    style=filled; color="{color}";')
            lines.extend(f'    "{label}";' for label in sorted(group))
            lines.append("  }")
        lines.extend(
            f'  "{label}";' for label in self.app_labels if label not in grouped_labels
        )
        for source, target in sorted(self.edges):
            if (source, target) in feedback:
                lines.append(f'  "{source}" -> "{target}" [color=red, penwidth=2];')
            else:
                lines.append(f'  "{source}" -> "{target}";')
        lines.append("}")
        return "\n".join(lines) + "\n"


def _strongly_connected_components(
    nodes: tuple[str, ...], adjacency: dict[str, list[str]]
) -> list[list[str]]:
    """Tarjan's algorithm, stdlib only -- one DFS pass, O(V+E)."""
    index_counter = [0]
    stack: list[str] = []
    on_stack: set[str] = set()
    indices: dict[str, int] = {}
    lowlink: dict[str, int] = {}
    sccs: list[list[str]] = []

    def strongconnect(v: str) -> None:
        indices[v] = index_counter[0]
        lowlink[v] = index_counter[0]
        index_counter[0] += 1
        stack.append(v)
        on_stack.add(v)

        for w in adjacency[v]:
            if w not in indices:
                strongconnect(w)
                lowlink[v] = min(lowlink[v], lowlink[w])
            elif w in on_stack:
                lowlink[v] = min(lowlink[v], indices[w])

        if lowlink[v] == indices[v]:
            component = []
            while True:
                w = stack.pop()
                on_stack.discard(w)
                component.append(w)
                if w == v:
                    break
            sccs.append(component)

    for v in nodes:
        if v not in indices:
            strongconnect(v)

    return sccs


def _feedback_edges_within_group(
    group: frozenset[str], adjacency: dict[str, list[str]]
) -> set[Edge]:
    """DFS restricted to one cycle group; an edge to a node already on the
    current DFS path is a back edge -- exactly the edge(s) closing a cycle."""
    visited: set[str] = set()
    on_path: set[str] = set()
    edges: set[Edge] = set()

    def dfs(v: str) -> None:
        visited.add(v)
        on_path.add(v)
        for w in adjacency[v]:
            if w not in group:
                continue
            if w in on_path:
                edges.add((v, w))
            elif w not in visited:
                dfs(w)
        on_path.discard(v)

    # min(), not next(iter(...)): group is a frozenset, whose iteration
    # order is hash-randomized per process -- picking the DFS root
    # deterministically keeps the result reproducible across runs.
    dfs(min(group))
    return edges


def _owning_app_label(module_name: str) -> str | None:
    """
    Which app (if any) owns a dotted module path -- delegating to Django's
    own `apps.get_containing_app_config`, which already resolves this
    correctly (including picking the most specific app for nested app
    names, e.g. "reporting.exporters.csv" belongs to app
    "reporting.exporters", not "reporting", when both are installed).
    """
    app_config = apps.get_containing_app_config(module_name)
    return app_config.label if app_config else None


def _module_name_for_file(app: AppConfig, file: Path) -> str:
    relative = file.relative_to(Path(app.path))
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join([app.name, *parts])


def _imported_modules(node: ast.AST, *, current_package: str) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        module: str | None
        if node.level:
            relative = "." * node.level + (node.module or "")
            try:
                module = importlib.util.resolve_name(relative, current_package)
            except (ImportError, ValueError):
                return []
        else:
            module = node.module
        return [module] if module else []
    return []


def _site_packages_dirs() -> tuple[Path, ...]:
    """
    The interpreter's own answer to "where do installed packages live",
    rather than guessing from folder-name conventions -- this is where
    Django itself, and ordinary (non-editable) third-party apps, actually
    get installed. Covers the running venv (wherever it lives, including
    nested inside the project) and `pip install --user`. Defensive
    `getattr` because `site.getsitepackages` is missing under some
    virtualenv/embedded-Python configurations.
    """
    dirs = list(getattr(site, "getsitepackages", lambda: [])())
    user_site = getattr(site, "getusersitepackages", lambda: None)()
    if user_site:
        dirs.append(user_site)
    return tuple(Path(d).resolve() for d in dirs)


def _is_local_app(app: AppConfig, site_packages_dirs: tuple[Path, ...]) -> bool:
    """
    An app "lives in your project" if its package isn't installed under
    one of `site_packages_dirs` -- i.e. not something pip put there as an
    ordinary (non-editable) dependency. Your own apps (and anything
    installed with `pip install -e .`) resolve to their real source
    location instead. Falls back to a folder-name check for the rare case
    `site_packages_dirs` came back empty.
    """
    path = Path(app.path).resolve()
    if site_packages_dirs:
        return not any(d == path or d in path.parents for d in site_packages_dirs)
    return "site-packages" not in path.parts and "dist-packages" not in path.parts


def _local_app_labels(app_configs: list[AppConfig]) -> frozenset[str]:
    site_packages_dirs = _site_packages_dirs()
    return frozenset(
        app.label for app in app_configs if _is_local_app(app, site_packages_dirs)
    )


def _matches_name_prefix(app_name: str, prefix: str) -> bool:
    """Dotted-path prefix match on app.name (not app.label -- nested apps'
    labels don't share a textual prefix the way their dotted names do).
    Boundary-aware: "myproject.reporting.exporters" must not also match a
    hypothetical "myproject.reporting.exporters_extra"."""
    return app_name == prefix or app_name.startswith(prefix + ".")


def _labels_under_name_prefixes(
    app_configs: list[AppConfig], prefixes: frozenset[str]
) -> frozenset[str]:
    return frozenset(
        app.label
        for app in app_configs
        if any(_matches_name_prefix(app.name, p) for p in prefixes)
    )


def _select_app_labels(
    app_configs: list[AppConfig],
    *,
    only: frozenset[str] | None,
    exclude: frozenset[str],
    exclude_external: bool,
    exclude_name_prefixes: frozenset[str],
) -> set[str]:
    """
    Start from `only` (or every installed app if `only` is None) -> drop
    external (non-local) apps if `exclude_external` -> drop every app whose
    dotted name falls under `exclude_name_prefixes` (for nested app subtrees
    like `reporting.exporters.**`, which are many distinct app labels
    sharing no common label prefix) -> drop `exclude`.
    """
    all_labels = frozenset(app.label for app in app_configs)
    unknown = ((only or frozenset()) | exclude) - all_labels
    if unknown:
        msg = f"unknown app label(s): {sorted(unknown)}"
        raise ValueError(msg)

    selected = set(only) if only is not None else set(all_labels)
    if exclude_external:
        selected &= _local_app_labels(app_configs)
    if exclude_name_prefixes:
        selected -= _labels_under_name_prefixes(app_configs, exclude_name_prefixes)
    selected -= exclude
    return selected


def _matches_any_file_pattern(file: Path, root: Path, patterns: frozenset[str]) -> bool:
    """
    fnmatch-style glob match, tried against both the bare filename (so
    "test*.py" matches regardless of where the file lives) and the path
    relative to the app root (so "migrations/*.py" or "*/fixtures/*.py"
    can target a specific location). No pattern is assumed or enforced --
    callers decide what "test", "generated", or "vendored" means for them.
    """
    if not patterns:
        return False
    relative = file.relative_to(root).as_posix()
    return any(
        fnmatch.fnmatchcase(file.name, pattern)
        or fnmatch.fnmatchcase(relative, pattern)
        for pattern in patterns
    )


def build_app_dependency_graph(
    *,
    only: frozenset[str] | None = None,
    exclude: frozenset[str] = frozenset(),
    exclude_external: bool = False,
    exclude_name_prefixes: frozenset[str] = frozenset(),
    exclude_file_patterns: frozenset[str] = frozenset(),
) -> AppDependencyGraph:
    """
    Walk every installed app's source, parse each file's imports via ast (no
    import side effects), and record every (source_app, target_app) edge
    where a file in one app imports something owned by another. Target
    ownership is resolved via `apps.get_containing_app_config`, which
    already picks the most specific app for nested app names (e.g.
    reporting.exporters.csv belongs to app reporting.exporters, not
    reporting, when both are installed).

    See `_select_app_labels` for node selection. An edge is kept only when
    both its source and target survive that selection -- this is a strict
    subgraph, not "included nodes plus dangling references to excluded
    ones."

    `exclude_file_patterns` drops any file matching one of the given
    fnmatch-style globs from the walk entirely, on both sides -- see
    `_matches_any_file_pattern`. Typical use is dropping test-only imports
    (fixtures, factories, mocks pulled in from other apps, which is a
    different kind of coupling than production code importing production
    code) with something like {"test*.py"}, but nothing about this option
    is specific to tests -- it's a plain file filter.
    """
    app_configs = list(apps.get_app_configs())
    selected = _select_app_labels(
        app_configs,
        only=only,
        exclude=exclude,
        exclude_external=exclude_external,
        exclude_name_prefixes=exclude_name_prefixes,
    )

    edges: set[Edge] = set()

    for source_app in app_configs:
        if source_app.label not in selected:
            continue
        root = Path(source_app.path)
        for file in root.rglob("*.py"):
            if _matches_any_file_pattern(file, root, exclude_file_patterns):
                continue
            try:
                tree = ast.parse(file.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue

            current_module = _module_name_for_file(source_app, file)
            current_package = (
                current_module
                if file.name == "__init__.py"
                else current_module.rpartition(".")[0]
            )

            for node in ast.walk(tree):
                for imported_module in _imported_modules(
                    node, current_package=current_package
                ):
                    target_app = _owning_app_label(imported_module)
                    if (
                        target_app
                        and target_app != source_app.label
                        and target_app in selected
                    ):
                        edges.add((source_app.label, target_app))

    return AppDependencyGraph(
        edges=frozenset(edges), app_labels=tuple(sorted(selected))
    )
