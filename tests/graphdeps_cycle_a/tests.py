# Fixture for testing graph_app_import_dependencies' --exclude-test-files
# (see tests/management/test_app_import_graph.py and
# tests/management/commands/test_graph_app_import_dependencies.py).
#
# This is the only file in this app that imports django_extensions, so
# toggling --exclude-test-files should make that edge appear/disappear
# without touching the graphdeps_cycle_a -> graphdeps_cycle_b edge from
# services.py. The import is inside a function for the same reason as
# services.py in this directory: ast sees it either way, but nothing
# actually executes it when pytest's --doctest-modules imports this
# module.


def touches_django_extensions():
    import django_extensions

    return django_extensions
