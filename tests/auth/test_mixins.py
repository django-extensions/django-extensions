from django.test import TestCase, RequestFactory
from django.db import models
from django.http import HttpResponse
from django.views.generic import View
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied

from django_extensions.auth.mixins import ModelUserFieldPermissionMixin

from testapp.models import HasOwnerModel


class EmptyResponseView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse()

class OwnerView(ModelUserFieldPermissionMixin, EmptyResponseView):
    model_permission_user_field = 'owner'

class ModelUserFieldPermissionMixinTests(TestCase):
    
    factory = RequestFactory()
    User = get_user_model()
    
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username="Joe", password="pass")
        cls.ownerModel = HasOwnerModel.objects.create(owner = cls.user)

    # Test if owner model has access
    def test_permission_pass(self):
        request = self.factory.get('/permission-required')
        request.user = self.user
        resp = OwnerView.as_view()(request)
        self.assertEqual(resp.status_code, 200)

    # Test if non owner model is redirected
    def test_permissioned_denied_redirect(self):
        request = self.factory.get('/permission-required')
        request.user = self.user
        with self.assertRaises(PermissionDenied):
            OwnerView.as_view()(request)
        
        request.user = AnonymousUser()
        resp = OwnerView.as_view()(request)
        self.assertEqual(resp.status_code, 302)