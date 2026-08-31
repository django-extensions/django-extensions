# Fixture proving --exclude-file-pattern can target a specific path
# location, not just a bare filename (see
# tests/management/test_app_import_graph.py). This is the only file in
# graphdeps_cycle_a that imports django.contrib.auth, so excluding by
# "nested/*.py" -- a pattern that only matches via the path relative to
# the app root -- should remove exactly that edge.


def touches_auth():
    from django.contrib.auth import models as auth_models

    return auth_models
