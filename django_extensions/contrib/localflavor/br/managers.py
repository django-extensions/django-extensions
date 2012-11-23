#!/usr/bin/env python
#-*- coding:utf-8 -*-

import datetime

from django.db.models import Q
from django.db import models


class BRPublisherModelManager(models.Manager):

    def publicados(self):
        now = datetime.datetime.now()
        qset = super(BRPublisherModelManager, self).filter(
            Q(publicado=True),
            Q(data_publicacao__lte=now),
            Q(data_expiracao__isnull=True) | Q(data_expiracao__gt=now))
        return qset
