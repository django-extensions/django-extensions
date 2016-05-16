# coding=utf-8
"""
Django Extensions abstract base model classes.
"""
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import (
    AutoSlugField, CreationDateTimeField, ModificationDateTimeField,
)

try:
    from django.utils.timezone import now as datetime_now
    assert datetime_now
except ImportError:
    import datetime
    datetime_now = datetime.datetime.now


class TimeStampedModel(models.Model):
    """ TimeStampedModel
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


class TitleDescriptionModel(models.Model):
    """ TitleDescriptionModel
    An abstract base class model that provides title and description fields.
    """
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True, null=True)

    class Meta:
        abstract = True


class TitleSlugDescriptionModel(TitleDescriptionModel):
    """ TitleSlugDescriptionModel
    An abstract base class model that provides title and description fields
    and a self-managed "slug" field that populates from the title.
    """
    slug = AutoSlugField(_('slug'), populate_from='title')

    class Meta:
        abstract = True


class ActivatorQuerySet(models.query.QuerySet):
    """ ActivatorQuerySet
    Query set that returns statused results
    """
    def active(self):
        """ Returns active query set """
        return self.filter(status=ActivatorModel.ACTIVE_STATUS)

    def inactive(self):
        """ Returns inactive query set """
        return self.filter(status=ActivatorModel.INACTIVE_STATUS)


class ActivatorModelManager(models.Manager):
    """ ActivatorModelManager
    Manager to return instances of ActivatorModel: SomeModel.objects.active() / .inactive()
    """
    def get_query_set(self):
        """ Proxy to `get_queryset`, drop this when Django < 1.6 is no longer supported """
        return self.get_queryset()

    def get_queryset(self):
        """ Use ActivatorQuerySet for all results """
        return ActivatorQuerySet(model=self.model, using=self._db)

    def active(self):
        """ Returns active instances of ActivatorModel: SomeModel.objects.active(),
        proxy to ActivatorQuerySet.active """
        return self.get_query_set().active()

    def inactive(self):
        """ Returns inactive instances of ActivatorModel: SomeModel.objects.inactive(),
        proxy to ActivatorQuerySet.inactive """
        return self.get_query_set().inactive()


class ActivatorModel(models.Model):
    """ ActivatorModel
    An abstract base class model that provides activate and deactivate fields.
    """
    INACTIVE_STATUS, ACTIVE_STATUS = range(2)
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
            self.activate_date = datetime_now()
        super(ActivatorModel, self).save(*args, **kwargs)
