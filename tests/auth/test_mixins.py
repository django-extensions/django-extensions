# -*- coding: utf-8 -*-
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.views.generic import DetailView
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from django_extensions.auth.mixins import ModelUserFieldPermissionMixin

from tests.testapp.models import HasOwnerModel


class EmptyResponseView(DetailView):
    model = HasOwnerModel

    def get(self, request, *args, **kwargs):
        return HttpResponse()


class OwnerView(ModelUserFieldPermissionMixin, EmptyResponseView):
    model_permission_user_field = 'owner'


class ModelUserFieldPermissionMixinTests(TestCase):
    factory = RequestFactory()
    User = get_user_model()

    @classmethod
    def setUpTestData(cls):
        cls.user = cls.User.objects.create(username="Joe", password="pass")
        cls.second_user = cls.User.objects.create(username="Jen",
                                                  password="pass")
        cls.ownerModel = HasOwnerModel.objects.create(owner=cls.user)
        cls.second_ownerModel = HasOwnerModel.objects.create(
            owner=cls.second_user)

    # Test if owner model has access
    def test_permission_pass(self):
        request = self.factory.get('/permission-required/')
        request.user = self.user
        resp = OwnerView.as_view()(request, pk=self.ownerModel.id)
        self.assertEqual(resp.status_code, 200)

    # # Test if anonymous user is redirected to login page
    def test_anonymous_redirect_to_login(self):
        request = self.factory.get('/permission-required/')
        request.user = AnonymousUser()
        resp = OwnerView.as_view()(request, pk=self.ownerModel.id)
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp.url,
                         "/accounts/login/?next=/permission-required/")

    def test_permission_denied(self):
        request = self.factory.get('/permission-required/', follow=True)
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            OwnerView.as_view()(request, pk=self.second_ownerModel.id)
