# -*- coding: utf-8 -*-
from unittest.mock import Mock

from django.test import RequestFactory, TestCase
from factory import Iterator

from django_extensions.admin.filter import NotNullFieldListFilter, NullFieldListFilter

from .testapp.factories import SecretFactory
from .testapp.models import Secret


class BaseFieldFilter(TestCase):
    """Base class for filter test cases."""

    @classmethod
    def setUpClass(cls):
        SecretFactory.create_batch(5, text=Iterator([None, None, 'foo', 'bar', None]))
        cls.request = RequestFactory().get('/admin/testapp/secret')
        cls.field = Secret._meta.get_field('text')
        cls.field_path = 'text'
        cls.qs = Secret.objects.all()

    @classmethod
    def tearDownClass(cls):
        Secret.objects.all().delete()


class NullFieldListFilterTests(BaseFieldFilter):
    """Tests for NullFieldListFilter."""

    def test_should_not_filter_qs_if_all_lookup_selected(self):
        params = {}
        filter_spec = NullFieldListFilter(self.field, self.request, params, Secret, Mock(), self.field_path)

        result = filter_spec.queryset(self.request, self.qs)

        self.assertQuerysetEqual(self.qs, map(repr, result), ordered=False)

    def test_should_return_objects_with_empty_text_if_yes_lookup_selected(self):
        expected_result = Secret.objects.filter(text__isnull=True)
        params = {'text__isnull': '1'}
        filter_spec = NullFieldListFilter(self.field, self.request, params, Secret, Mock(), self.field_path)

        result = filter_spec.queryset(self.request, self.qs)

        self.assertQuerysetEqual(expected_result, map(repr, result), ordered=False)

    def test_should_return_objects_with_not_empty_text_value_if_no_lookup_selected(self):
        expected_result = Secret.objects.filter(text__isnull=False)
        params = {'text__isnull': '0'}
        filter_spec = NullFieldListFilter(self.field, self.request, params, Secret, Mock(), self.field_path)

        result = filter_spec.queryset(self.request, self.qs)

        self.assertQuerysetEqual(expected_result, map(repr, result), ordered=False)

    def test_choices(self):
        expected_result = [
            {'selected': True, 'query_string': '?', 'display': 'All'},
            {'selected': False, 'query_string': '?active__isnull=1', 'display': 'Yes'},
            {'selected': False, 'query_string': '?active__isnull=0', 'display': 'No'},
        ]
        m_cl = Mock()
        m_cl.get_query_string.side_effect = ['?', '?active__isnull=1', '?active__isnull=0']
        filter_spec = NullFieldListFilter(self.field, self.request, {}, Secret, Mock(), self.field_path)

        result = filter_spec.choices(m_cl)

        self.assertEqual(list(result), expected_result)


class NotNullFieldListFilterTests(BaseFieldFilter):
    """Tests for NotNullFieldListFilter."""

    def test_should_not_filter_qs_if_all_lookup_selected(self):
        params = {}
        filter_spec = NotNullFieldListFilter(self.field, self.request, params, Secret, Mock(), self.field_path)

        result = filter_spec.queryset(self.request, self.qs)

        self.assertQuerysetEqual(self.qs, map(repr, result), ordered=False)
