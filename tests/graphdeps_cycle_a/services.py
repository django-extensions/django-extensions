# Fixture for testing graph_app_import_dependencies' cycle detection
# (see tests/management/commands/test_graph_app_import_dependencies.py).
#
# The import below is deliberately inside a function, not at module level:
# the command finds it by parsing this file's ast (which sees imports at
# any nesting level), so the cycle is visible to the graph without this
# module ever actually executing a real circular import -- which matters
# because pytest's --doctest-modules setting imports every .py module it
# collects, including this one.


def use_b():
    from tests.graphdeps_cycle_b import services as b_services

    return b_services
