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
        cls.ownerModel = HasOwnerModel.objects.create(owner=cls.user)

    # Test if owner model has access
    def test_permission_pass(self):
        request = self.factory.get('/permission-required/' + str(self.ownerModel.id))
        request.user = self.user
        resp = OwnerView.as_view()(request)
        self.assertEqual(resp.status_code, 200)

    # # Test if non owner model is redirected
    def test_permission_denied_and_redirect(self):
        request = self.factory.get('/permission-required/' + str(self.ownerModel.id))
        request.user = AnonymousUser()
        resp = OwnerView.as_view()(request)
        self.assertRaises(PermissionDenied)
        self.assertEqual(resp.status_code, 302)
