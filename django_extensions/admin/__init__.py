#
#    Autocomplete feature for admin panel
#
#    Most of the code has been written by Jannis Leidel and was updated a bit
#    for django_extensions.
#    http://jannisleidel.com/2008/11/autocomplete-form-widget-foreignkey-model-fields/
#
#    to_string_function, Satchmo adaptation and some comments added by emes
#    (Michal Salaban)
#
from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext as _
from django.utils.text import get_text_list
from django.conf import settings

from django_extensions.admin.widgets import AdminForeignKeySearchInput
from django_extensions.views.autocomplete import foreignkey_autocomplete

class ForeignKeyAutocompleteAdmin(admin.ModelAdmin):
    """Admin class for models using the autocomplete feature.

    There are two additional fields:
       - related_search_fields: defines fields of managed model that
         have to be represented by autocomplete input, together with
         a list of target model fields that are searched for
         input string, e.g.:
         
         related_search_fields = {
            'author': ('first_name', 'email'),
         }

       - related_string_functions: contains optional functions which
         take target model instance as only argument and return string
         representation. By default __unicode__() method of target
         object is used.

         related_string_functions = {
            'author': lambda u: u.get_full_name(),
         }
    """

    related_search_fields = getattr(settings,
        'DJANGO_EXTENSIONS_FOREIGNKEY_AUTOCOMPLETE_SEARCH_FIELDS', {})
    related_string_functions = getattr(settings,
        'DJANGO_EXTENSIONS_FOREIGNKEY_AUTOCOMPLETE_STRING_FUNCTIONS', {})

    def __call__(self, request, url):
        if url is None:
            pass
        elif url == 'foreignkey_autocomplete':
            return foreignkey_autocomplete(request, self.related_string_functions)
        return super(ForeignKeyAutocompleteAdmin, self).__call__(request, url)

    def get_help_text(self, field_name, model_name):
        searchable_fields = self.related_search_fields.get(field_name, None)
        if searchable_fields:
            help_kwargs = {
                'model_name': model_name,
                'field_list': get_text_list(searchable_fields, _('and')),
            }
            return _('Use the left field to do %(model_name)s lookups '
                     'in the fields %(field_list)s.') % help_kwargs
        return ''

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Overrides the default widget for Foreignkey fields if they are
        specified in the related_search_fields class attribute.
        """
        if (isinstance(db_field, models.ForeignKey) and 
                db_field.name in self.related_search_fields):
            model_name = db_field.rel.to._meta.object_name
            help_text = self.get_help_text(db_field.name, model_name)
            if kwargs.get('help_text'):
                help_text = u'%s %s' % (kwargs['help_text'], help_text)
            kwargs['widget'] = AdminForeignKeySearchInput(db_field.rel,
                                    self.related_search_fields[db_field.name])
            kwargs['help_text'] = help_text
        return super(ForeignKeyAutocompleteAdmin,
            self).formfield_for_dbfield(db_field, **kwargs)
