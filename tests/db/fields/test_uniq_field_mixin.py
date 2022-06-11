# -*- coding: utf-8 -*-
from unittest import mock

from django.db import models
from django.test import TestCase
from tests.testapp.models import (
    DummyRelationModel, InheritedFromPostWithUniqField, PostWithUniqField,
    ReverseModel, SecondDummyRelationModel, ThirdDummyRelationModel,
)

from django_extensions.db.fields import UniqueFieldMixin


class UniqFieldMixinTestCase(TestCase):
    def setUp(self):

        class MockField(UniqueFieldMixin):
            def __init__(self, **kwargs):
                for key, value in kwargs.items():
                    setattr(self, key, value)

        self.uniq_field = MockField(
            attname='uniq_field',
            max_length=255,
            boolean_attr=True,
            non_boolean_attr='non_boolean_attr'
        )

        f_dummy = DummyRelationModel.objects.create()
        s_dummy = SecondDummyRelationModel.objects.create()
        t_dummy = ThirdDummyRelationModel.objects.create()

        post = PostWithUniqField.objects.create(
            uniq_field='test_uniq',
            common_field='first',
            another_common_field='second',
            many_to_one_field=f_dummy,
            one_to_one_field=s_dummy,
        )
        post.many_to_many_field.add(t_dummy)
        post.save()

        ReverseModel.objects.create(post_field=post)

        self.post = post

    def tearDown(self):
        PostWithUniqField.objects.all().delete()
        DummyRelationModel.objects.all().delete()
        SecondDummyRelationModel.objects.all().delete()
        ThirdDummyRelationModel.objects.all().delete()
        ReverseModel.objects.all().delete()

    def test_check_is_bool_boolean_attr(self):

        self.assertIsNone(self.uniq_field.check_is_bool('boolean_attr'))

    def test_check_is_bool_non_boolean_attr(self):
        with self.assertRaisesMessage(
            ValueError,
            "'non_boolean_attr' argument must be True or False",
        ):
            self.uniq_field.check_is_bool('non_boolean_attr')

    def test__get_fields_returns_list_of_tulpes(self):
        uniq_mixin_fields = UniqueFieldMixin._get_fields(PostWithUniqField)
        self.assertIsInstance(uniq_mixin_fields, list)
        for field in uniq_mixin_fields:
            self.assertIsInstance(field, tuple)

    def test__get_fields_returns_correct_fields(self):
        option_fields = PostWithUniqField._meta.get_fields()
        uniq_mixin_fields = [i[0] for i in UniqueFieldMixin._get_fields(PostWithUniqField)]

        self.assertEqual(len(option_fields), 9)
        self.assertEqual(len(uniq_mixin_fields), 7)

        fields_to_be_excluded_from_uniq_mixin_fields = [
            f for f in option_fields
            if f.is_relation and not f.one_to_one and not (f.many_to_one and f.related_model)
        ]

        for field in fields_to_be_excluded_from_uniq_mixin_fields:
            self.assertNotIn(field, uniq_mixin_fields)

    def test__get_fields_returns_correct_model(self):
        post_models = [i[1] for i in UniqueFieldMixin._get_fields(PostWithUniqField)]
        self.assertTrue(all(model is None for model in post_models))

        inherited_post_models = [
            i[1] for i
            in UniqueFieldMixin._get_fields(InheritedFromPostWithUniqField)
            if i[1]
        ]

        self.assertEqual(len(inherited_post_models), 6)
        self.assertTrue(all(model is PostWithUniqField) for model in inherited_post_models)

    def test_get_queryset(self):
        mocked_get_fields = (
            (models.CharField, PostWithUniqField),
        )
        with mock.patch(
            'django_extensions.db.fields.UniqueFieldMixin._get_fields',
            return_value=mocked_get_fields
        ), mock.patch(
            'tests.testapp.models.PostWithUniqField._default_manager.all'
        ) as mocked_qs_all:

            self.uniq_field.get_queryset(PostWithUniqField, models.CharField)

        mocked_qs_all.assert_called_with()

        mocked_get_fields = (
            (models.CharField, None),
        )

        with mock.patch(
            'django_extensions.db.fields.UniqueFieldMixin._get_fields',
            return_value=mocked_get_fields
        ), mock.patch(
            'tests.testapp.models.InheritedFromPostWithUniqField._default_manager.all'
        ) as mocked_qs_all:

            self.uniq_field.get_queryset(InheritedFromPostWithUniqField, models.CharField)

        mocked_qs_all.assert_called_with()

    def test_find_unique(self):
        def filter_func(*args, **kwargs):
            uniq_field = kwargs.get('uniq_field')
            if uniq_field == 'a':
                return mocked_qs
            return None

        mocked_qs = mock.Mock(spec=PostWithUniqField.objects)
        mocked_qs.filter.side_effect = filter_func
        mocked_qs.exclude.return_value = mocked_qs

        field = models.CharField
        with mock.patch(
            'django_extensions.db.fields.UniqueFieldMixin.get_queryset',
            return_value=mocked_qs
        ) as get_qs:

            res = self.uniq_field.find_unique(self.post, field, iter('abcde'))

        get_qs.assert_called_with(PostWithUniqField, field)
        mocked_qs.exclude.assert_called_with(pk=self.post.pk)
        self.assertEqual(res, 'b')
        self.assertTrue(hasattr(self.post, 'uniq_field'))
        self.assertEqual(self.post.uniq_field, 'b')
