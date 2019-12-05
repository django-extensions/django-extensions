# -*- coding: utf-8 -*-
import pytest


@pytest.fixture(scope="session")
def django_db_use_migrations(request):
    return True
