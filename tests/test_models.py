# coding=utf-8
import pytest

from .testapp.models import Post

pytestmark = pytest.mark.django_db


def test_active_includes_active(active_post):
    assert active_post in Post.objects.active()


def test_active_excludes_inactive(inactive_post):
    assert inactive_post not in Post.objects.active()


def test_inactive_includes_inactive(inactive_post):
    assert inactive_post in Post.objects.inactive()


def test_inactive_excludes_active(active_post):
    assert active_post not in Post.objects.inactive()


def test_chainable(active_post):
    assert active_post in Post.objects.filter(title='Foo').active()


def test_inactive_is_chainable(inactive_post):
    assert inactive_post in Post.objects.filter(title='Foo').inactive()
