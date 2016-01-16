# coding: utf-8
import fnmatch
import os

import pytest

from django_extensions.db.models import ActivatorModel

from .testapp.models import Post


@pytest.fixture
def active_post():
    return Post.objects.create(title='Foo', status=ActivatorModel.ACTIVE_STATUS)


@pytest.fixture
def inactive_post():
    return Post.objects.create(title='Foo', status=ActivatorModel.INACTIVE_STATUS)


def find_pyc(path, mask='*.pyc'):
    return [
        os.path.join(root, filename)
        for root, dirs, filenames in os.walk(path)
        for filename in fnmatch.filter(filenames, mask)
    ]
