# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.admin import FieldListFilter
try:
    from django.contrib.admin.utils import prepare_lookup_value
except ImportError:
    # django < 1.7
    from django.contrib.admin.util import prepare_lookup_value
from django.utils.translation import ugettext_lazy as _


class NullFieldListFilter(FieldListFilter):
    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = '{0}__isnull'.format(field_path)
        super(NullFieldListFilter, self).__init__(field, request, params, model, model_admin, field_path)
        lookup_choices = self.lookups(request, model_admin)
        self.lookup_choices = () if lookup_choices is None else list(lookup_choices)

    def expected_parameters(self):
        return [self.lookup_kwarg]

    def value(self):
        return self.used_parameters.get(self.lookup_kwarg, None)

    def lookups(self, request, model_admin):
        return (
            ('1', _('Yes')),
            ('0', _('No')),
        )

    def choices(self, cl):
        yield {
            'selected': self.value() is None,
            'query_string': cl.get_query_string({}, [self.lookup_kwarg]),
            'display': _('All'),
        }
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == prepare_lookup_value(self.lookup_kwarg, lookup),
                'query_string': cl.get_query_string({
                    self.lookup_kwarg: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() is not None:
            kwargs = {self.lookup_kwarg: self.value()}
            return queryset.filter(**kwargs)
        return queryset


class NotNullFieldListFilter(NullFieldListFilter):
    def lookups(self, request, model_admin):
        return (
            ('0', _('Yes')),
            ('1', _('No')),
        )
