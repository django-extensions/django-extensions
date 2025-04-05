# -*- coding: utf-8 -*-
import datetime

from django.utils.translation import gettext_lazy as _
from mongoengine.document import Document
from mongoengine.fields import DateTimeField, IntField, StringField
from mongoengine.queryset import QuerySetManager

from django_extensions.mongodb.fields import (
    AutoSlugField,
    CreationDateTimeField,
    ModificationDateTimeField,
)


class TimeStampedModel(Document):
    """
    TimeStampedModel

    An abstract base class model that provides self-managed "created" and
    "modified" fields.
    """

    created = CreationDateTimeField()
    modified = ModificationDateTimeField()

    class Meta:
        abstract = True


class TitleSlugDescriptionModel(Document):
    """
    TitleSlugDescriptionModel

    An abstract base class model that provides title and description fields
    and a self-managed "slug" field that populates from the title.
    """

    title = StringField(max_length=255)
    slug = AutoSlugField(populate_from="title")
    description = StringField(blank=True, null=True)

    class Meta:
        abstract = True


class ActivatorModelManager(QuerySetManager):
    """
    ActivatorModelManager

    Manager to return instances of ActivatorModel:
        SomeModel.objects.active() / .inactive()
    """

    def active(self):
        """
        Return active instances of ActivatorModel:

        SomeModel.objects.active()
        """
        return super().get_queryset().filter(status=1)

    def inactive(self):
        """
        Return inactive instances of ActivatorModel:

        SomeModel.objects.inactive()
        """
        return super().get_queryset().filter(status=0)


class ActivatorModel(Document):
    """
    ActivatorModel

    An abstract base class model that provides activate and deactivate fields.
    """

    STATUS_CHOICES = (
        (0, _("Inactive")),
        (1, _("Active")),
    )
    status = IntField(choices=STATUS_CHOICES, default=1)
    activate_date = DateTimeField(
        blank=True, null=True, help_text=_("keep empty for an immediate activation")
    )
    deactivate_date = DateTimeField(
        blank=True, null=True, help_text=_("keep empty for indefinite activation")
    )
    objects = ActivatorModelManager()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.activate_date:
            self.activate_date = datetime.datetime.now()
        super().save(*args, **kwargs)
