# -*- coding: utf-8 -*-

from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import AutoSlugField, CreationDateTimeField, ModificationDateTimeField


class TimeStampedModel(models.Model):
    """
    TimeStampedModel

    An abstract base class model that provides self-managed "created" and
    "modified" fields.
    """

    created = CreationDateTimeField(_('created'))
    modified = ModificationDateTimeField(_('modified'))

    def save(self, **kwargs):
        self.update_modified = kwargs.pop('update_modified', getattr(self, 'update_modified', True))
        super(TimeStampedModel, self).save(**kwargs)

    class Meta:
        get_latest_by = 'modified'
        ordering = ('-modified', '-created',)
        abstract = True


class IndexedTimeStampedModel(TimeStampedModel):
    """
    IndexedTimeStampedModel

    An abstract base class model that provides self-managed "created" and
    "modified" fields with db indices on them.
    """
    class Meta(TimeStampedModel.Meta):
        indexes = [
            models.Index(fields=["-created", "-modified"]),
            models.Index(fields=["-created"]), models.Index(fields=["-modified"])
        ]
        abstract = True


class TitleDescriptionModel(models.Model):
    """
    TitleDescriptionModel

    An abstract base class model that provides title and description fields.
    """

    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)

    class Meta:
        abstract = True


class IndexedTitleDescriptionModel(TitleDescriptionModel):
    """
    IndexedTitleDescriptionModel

    An abstract base class model that provides title and description fields
    with an index on title field.
    """
    class Meta(TitleDescriptionModel.Meta):
        indexes = [
            models.Index(fields=["title"]),
        ]
        abstract = True


class TitleSlugDescriptionModel(TitleDescriptionModel):
    """
    TitleSlugDescriptionModel

    An abstract base class model that provides title and description fields
    and a self-managed "slug" field that populates from the title.

    .. note ::
        If you want to use custom "slugify" function, you could
        define ``slugify_function`` which then will be used
        in :py:class:`AutoSlugField` to slugify ``populate_from`` field.

        See :py:class:`AutoSlugField` for more details.
    """

    slug = AutoSlugField(_('slug'), populate_from='title')

    class Meta:
        abstract = True


class IndexedTitleSlugDescriptionModel(TitleSlugDescriptionModel):
    """
    IndexedTitleSlugDescriptionModel

    An abstract base class model that provides title and description fields
    and a self-managed "slug" field that populates from the title with indexes
    on "title" and "slug" fields.
    """
    class Meta(TitleSlugDescriptionModel.Meta):
        indexes = [
            models.Index(fields=["title", "slug"]),
            models.Index(fields=["title"]), models.Index(fields=["slug"])
        ]
        abstract = True


class ActivatorQuerySet(models.query.QuerySet):
    """
    ActivatorQuerySet

    Query set that returns statused results
    """

    def active(self):
        """ Return active query set """
        return self.filter(status=ActivatorModel.ACTIVE_STATUS)

    def inactive(self):
        """ Return inactive query set """
        return self.filter(status=ActivatorModel.INACTIVE_STATUS)


class ActivatorModelManager(models.Manager):
    """
    ActivatorModelManager

    Manager to return instances of ActivatorModel: SomeModel.objects.active() / .inactive()
    """

    def get_queryset(self):
        """ Use ActivatorQuerySet for all results """
        return ActivatorQuerySet(model=self.model, using=self._db)

    def active(self):
        """
        Return active instances of ActivatorModel:

        SomeModel.objects.active(), proxy to ActivatorQuerySet.active
        """
        return self.get_queryset().active()

    def inactive(self):
        """
        Return inactive instances of ActivatorModel:

        SomeModel.objects.inactive(), proxy to ActivatorQuerySet.inactive
        """
        return self.get_queryset().inactive()


class ActivatorModel(models.Model):
    """
    ActivatorModel

    An abstract base class model that provides activate and deactivate fields.
    """

    INACTIVE_STATUS = 0
    ACTIVE_STATUS = 1

    STATUS_CHOICES = (
        (INACTIVE_STATUS, _('Inactive')),
        (ACTIVE_STATUS, _('Active')),
    )
    status = models.IntegerField(_('status'), choices=STATUS_CHOICES, default=ACTIVE_STATUS)
    activate_date = models.DateTimeField(blank=True, null=True, help_text=_('keep empty for an immediate activation'))
    deactivate_date = models.DateTimeField(blank=True, null=True, help_text=_('keep empty for indefinite activation'))
    objects = ActivatorModelManager()

    class Meta:
        ordering = ('status', '-activate_date',)
        abstract = True

    def save(self, *args, **kwargs):
        if not self.activate_date:
            self.activate_date = now()
        super(ActivatorModel, self).save(*args, **kwargs)


class IndexedActivatorModel(ActivatorModel):
    """
    ActivatorModel

    An abstract base class model that provides activate and deactivate fields
    with indexes on "activate_date" and "deactivate_date".
    """

    class Meta(ActivatorModel.Meta):
        indexes = [
            models.Index(fields=["-activate_date", "-deactivate_date"]),
            models.Index(fields=["-activate_date"]),
            models.Index(fields=["-deactivate_date"])
        ]
        abstract = True
