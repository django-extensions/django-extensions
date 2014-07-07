from django.db import models

from django_extensions.db.models import ActivatorModel
from django_extensions.db.fields import AutoSlugField
from django_extensions.db.fields import UUIDField
from django_extensions.db.fields import ShortUUIDField
from django_extensions.db.fields.json import JSONField


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
    name = models.ForeignKey(Name)
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


class JSONFieldTestModel(models.Model):
    a = models.IntegerField()
    j_field = JSONField()

    class Meta:
        app_label = 'django_extensions'


class UUIDTestModel_field(models.Model):
    a = models.IntegerField()
    uuid_field = UUIDField()

    class Meta:
        app_label = 'django_extensions'


class UUIDTestModel_pk(models.Model):
    uuid_field = UUIDField(primary_key=True)

    class Meta:
        app_label = 'django_extensions'


class UUIDTestAgregateModel(UUIDTestModel_pk):
    a = models.IntegerField()

    class Meta:
        app_label = 'django_extensions'


class UUIDTestManyToManyModel(UUIDTestModel_pk):
    many = models.ManyToManyField(UUIDTestModel_field)

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
