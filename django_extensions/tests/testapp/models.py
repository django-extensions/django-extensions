from django.db import models

from django_extensions.db.models import ActivatorModel
from django_extensions.db.fields import AutoSlugField
from django_extensions.db.fields import UUIDField
from django_extensions.db.fields import ShortUUIDField
from django_extensions.db.fields.json import JSONField


class Secret(models.Model):
    name = models.CharField(blank=True, max_length=255, null=True)
    text = models.TextField(blank=True, null=True)


class Name(models.Model):
    name = models.CharField(max_length=50)


class Note(models.Model):
    note = models.TextField()


class Person(models.Model):
    name = models.ForeignKey(Name)
    age = models.PositiveIntegerField()
    children = models.ManyToManyField('self')
    notes = models.ManyToManyField(Note)


class Post(ActivatorModel):
    title = models.CharField(max_length=255)


class SluggedTestModel(models.Model):
    title = models.CharField(max_length=42)
    slug = AutoSlugField(populate_from='title')


class ChildSluggedTestModel(SluggedTestModel):
    pass


class JSONFieldTestModel(models.Model):
    a = models.IntegerField()
    j_field = JSONField()


class UUIDTestModel_field(models.Model):
    a = models.IntegerField()
    uuid_field = UUIDField()


class UUIDTestModel_pk(models.Model):
    uuid_field = UUIDField(primary_key=True)


class UUIDTestAgregateModel(UUIDTestModel_pk):
    a = models.IntegerField()


class UUIDTestManyToManyModel(UUIDTestModel_pk):
    many = models.ManyToManyField(UUIDTestModel_field)


class ShortUUIDTestModel_field(models.Model):
    a = models.IntegerField()
    uuid_field = ShortUUIDField()


class ShortUUIDTestModel_pk(models.Model):
    uuid_field = ShortUUIDField(primary_key=True)


class ShortUUIDTestAgregateModel(ShortUUIDTestModel_pk):
    a = models.IntegerField()


class ShortUUIDTestManyToManyModel(ShortUUIDTestModel_pk):
    many = models.ManyToManyField(ShortUUIDTestModel_field)
