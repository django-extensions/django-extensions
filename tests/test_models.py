# -*- coding: utf-8 -*-
from django.test import TestCase

from django_extensions.db.models import ActivatorModel

from .testapp.models import Post


class ActivatorModelTestCase(TestCase):
    def test_active_includes_active(self):
        post = Post.objects.create(status=ActivatorModel.ACTIVE_STATUS)
        active = Post.objects.active()
        self.assertIn(post, active)
        post.delete()

    def test_active_excludes_inactive(self):
        post = Post.objects.create(status=ActivatorModel.INACTIVE_STATUS)
        active = Post.objects.active()
        self.assertNotIn(post, active)
        post.delete()

    def test_inactive_includes_inactive(self):
        post = Post.objects.create(status=ActivatorModel.INACTIVE_STATUS)
        inactive = Post.objects.inactive()
        self.assertIn(post, inactive)
        post.delete()

    def test_inactive_excludes_active(self):
        post = Post.objects.create(status=ActivatorModel.ACTIVE_STATUS)
        inactive = Post.objects.inactive()
        self.assertNotIn(post, inactive)
        post.delete()

    def test_active_is_chainable(self):
        post = Post.objects.create(title='Foo', status=ActivatorModel.ACTIVE_STATUS)
        specific_post = Post.objects.filter(title='Foo').active()
        self.assertIn(post, specific_post)
        post.delete()

    def test_inactive_is_chainable(self):
        post = Post.objects.create(title='Foo', status=ActivatorModel.INACTIVE_STATUS)
        specific_post = Post.objects.filter(title='Foo').inactive()
        self.assertIn(post, specific_post)
        post.delete()
