#!/usr/bin/env python
#-*- coding:utf-8 -*-

import datetime

from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import \
    AutoSlugField, CreationDateTimeField, ModificationDateTimeField


from .managers import BRPublisherModelManager


class BRCreationModificationModel(models.Model):

    data_criacao = CreationDateTimeField(_(u'Data de criação'))
    data_modificacao = ModificationDateTimeField(_(u'Data de modificação'))

    class Meta:
        abstract = True


class BRTitleSlugCreationModificationModel(BRCreationModificationModel):

    titulo = models.CharField(_(u'Título'), max_length=255)
    slug = AutoSlugField(
        _('slug'), populate_from='titulo', overwrite=True, max_length=255,
        editable=False)

    def __unicode__(self):
        return self.titulo

    class Admin(admin.ModelAdmin):
        list_display = ("titulo", "slug", "data_criacao", "data_modificacao", )
        list_filter = ("data_criacao", "data_modificacao", )

    class Meta:
        abstract = True
        ordering = ("titulo",  )


class BRPublisherModel(models.Model):
    _HELP_TEXT = _(u'Deixe em branco para publicação imediata.')
    publicado = models.BooleanField(_('Publicado'), default=False)
    data_publicacao = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_HELP_TEXT,
        verbose_name=_(u'Data de publicação'))
    data_expiracao = models.DateTimeField(
        blank=True,
        null=True,
        help_text=_HELP_TEXT,
        verbose_name=_(u'Data de expiração'))

    objects = BRPublisherModelManager()

    class Meta:
        abstract = True
        ordering = ("-data_publicacao", "-publicado", )

    def is_publicado(self):
        now = datetime.datetime.now()
        return self.publicado and \
               self.data_publicacao <= now and \
               (self.data_expiracao is None or self.data_expiracao > now)

    def save(self, *args, **kwargs):
        if not self.data_publicacao:
            self.data_publicacao = datetime.datetime.now()
        return super(BRPublisherModel, self).save(*args, **kwargs)
