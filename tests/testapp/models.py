# -*- coding: utf-8 -*-
from django.db import models

from django_extensions.db.fields import (
    AutoSlugField,
    RandomCharField,
    ShortUUIDField,
)
from django_extensions.db.fields.json import JSONField
from django_extensions.db.models import ActivatorModel, TimeStampedModel


class Secret(models.Model):
    name = models.CharField(blank=True, max_length=255, null=True)
    text = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'django_extensions'


class Name(models.Model):
    name = models.CharField(max_length=50)

    class Meta:
        app_label = 'django_extensions'


class Note(models.Model):
    note = models.TextField()

    class Meta:
        app_label = 'django_extensions'


class Person(models.Model):
    name = models.ForeignKey(Name, on_delete=models.CASCADE)
    age = models.PositiveIntegerField()
    children = models.ManyToManyField('self')
    notes = models.ManyToManyField(Note)

    class Meta:
        app_label = 'django_extensions'


class Post(ActivatorModel):
    title = models.CharField(max_length=255)

    class Meta:
        app_label = 'django_extensions'


class SluggedTestModel(models.Model):
    title = models.CharField(max_length=42)
    slug = AutoSlugField(populate_from='title')

    class Meta:
        app_label = 'django_extensions'


class ChildSluggedTestModel(SluggedTestModel):
    class Meta:
        app_label = 'django_extensions'


class ModelMethodSluggedTestModel(models.Model):
    title = models.CharField(max_length=42)
    slug = AutoSlugField(populate_from='get_readable_title')

    class Meta:
        app_label = 'django_extensions'

    def get_readable_title(self):
        return "The title is {}".format(self.title)


class FKSluggedTestModel(models.Model):
    related_field = models.ForeignKey(SluggedTestModel, on_delete=models.CASCADE)
    slug = AutoSlugField(populate_from="related_field__title")

    class Meta:
        app_label = 'django_extensions'


class FKSluggedTestModelCallable(models.Model):
    related_field = models.ForeignKey(ModelMethodSluggedTestModel, on_delete=models.CASCADE)
    slug = AutoSlugField(populate_from="related_field__get_readable_title")

    class Meta:
        app_label = 'django_extensions'


class JSONFieldTestModel(models.Model):
    a = models.IntegerField()
    j_field = JSONField()

    class Meta:
        app_label = 'django_extensions'


class ShortUUIDTestModel_field(models.Model):
    a = models.IntegerField()
    uuid_field = ShortUUIDField()

    class Meta:
        app_label = 'django_extensions'


class ShortUUIDTestModel_pk(models.Model):
    uuid_field = ShortUUIDField(primary_key=True)

    class Meta:
        app_label = 'django_extensions'


class ShortUUIDTestAgregateModel(ShortUUIDTestModel_pk):
    a = models.IntegerField()

    class Meta:
        app_label = 'django_extensions'


class ShortUUIDTestManyToManyModel(ShortUUIDTestModel_pk):
    many = models.ManyToManyField(ShortUUIDTestModel_field)

    class Meta:
        app_label = 'django_extensions'


class RandomCharTestModel(models.Model):
    random_char_field = RandomCharField(length=8, unique=False)

    class Meta:
        app_label = 'django_extensions'


class RandomCharTestModelUnique(models.Model):
    random_char_field = RandomCharField(length=8, unique=True)

    class Meta:
        app_label = 'django_extensions'


class RandomCharTestModelAlphaDigits(models.Model):
    random_char_field = RandomCharField(length=8, unique=True)

    class Meta:
        app_label = 'django_extensions'


class RandomCharTestModelLowercaseAlphaDigits(models.Model):
    random_char_field = RandomCharField(length=8, lowercase=True)

    class Meta:
        app_label = 'django_extensions'
        verbose_name = 'lowercase alpha digits'


class RandomCharTestModelUppercaseAlphaDigits(models.Model):
    random_char_field = RandomCharField(length=8, uppercase=True)

    class Meta:
        app_label = 'django_extensions'
        verbose_name = 'uppercase alpha digits'


class RandomCharTestModelLowercase(models.Model):
    random_char_field = RandomCharField(length=8, lowercase=True, include_digits=False)

    class Meta:
        app_label = 'django_extensions'


class RandomCharTestModelUppercase(models.Model):
    random_char_field = RandomCharField(length=8, uppercase=True, include_digits=False)

    class Meta:
        app_label = 'django_extensions'


class RandomCharTestModelAlpha(models.Model):
    random_char_field = RandomCharField(length=8, include_digits=False)

    class Meta:
        app_label = 'django_extensions'


class RandomCharTestModelDigits(models.Model):
    random_char_field = RandomCharField(length=8, include_alpha=False)

    class Meta:
        app_label = 'django_extensions'


class RandomCharTestModelPunctuation(models.Model):
    random_char_field = RandomCharField(
        length=8,
        include_punctuation=True,
        include_digits=False,
        include_alpha=False,
    )

    class Meta:
        app_label = 'django_extensions'


class TimestampedTestModel(TimeStampedModel):
    class Meta:
        app_label = 'django_extensions'


class Permission(models.Model):
    text = models.CharField(max_length=32)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)


class UniqueTestAppModel(models.Model):
    global_id = models.CharField(max_length=32, unique=True)
