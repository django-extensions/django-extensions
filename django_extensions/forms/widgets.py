from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import ImproperlyConfigured
from django.utils.safestring import mark_safe
from django.utils.text import truncate_words
from django.template.loader import render_to_string
from django.contrib.admin.widgets import ForeignKeyRawIdWidget

JQUERY_URL = getattr(settings, 'JQUERY_URL', 'django_extensions/js/jquery.js')

class ForeignKeySearchInput(forms.TextInput):
    """
    A Widget for displaying ForeignKeys in an autocomplete search input
    instead in a <select> box.
    """
    # Set in subclass to render the widget with a different template
    widget_template = None
    # Set this to the patch of the search view
    search_path = None

    class Media:
        css = {
            'all': ('django_extensions/css/jquery.autocomplete.css',)
        }
        js = (JQUERY_URL,
            'django_extensions/js/jquery.bgiframe.min.js',
            'django_extensions/js/jquery.ajaxQueue.js',
            'django_extensions/js/jquery.autocomplete.js',
        )

    def __init__(self, field_name, model, search_fields=None, attrs=None):
        super(ForeignKeySearchInput, self).__init__(attrs)
        self.model = model
        self.field_name = field_name
        self.related_search_fields = search_fields
        if search_fields is None:
            search_fields = getattr(settings,
                'DJANGO_EXTENSIONS_FOREIGNKEY_AUTOCOMPLETE_SEARCH_FIELDS', {})
        self.searchable_fields = search_fields.get(field_name, "")

    def label_for_value(self, value):
        obj = self.target._default_manager.get(**{self.field_name: value})
        return truncate_words(obj, 14)

    def get_help_text(self, field_name, model_name):
        if self.searchable_fields:
            help_kwargs = {
                'model_name': model_name,
                'field_list': get_text_list(searchable_fields, _('and')),
            }
            return _('Use the left field to do %(model_name)s lookups '
                     'in the fields %(field_list)s.') % help_kwargs
        return ''

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        opts = self.model._meta
        app_label = opts.app_label
        model_name = opts.object_name.lower()
        output = [super(ForeignKeySearchInput, self).render(name, value, attrs)]
        if value:
            label = self.label_for_value(value)
        else:
            label = u''
        if self.search_path is None:
            try:
                self.search_path = reverse('foreignkey_autocomplete')
            except NoReverseMatch:
                raise ImproperlyConfigured(
                    "The foreignkey autocomplete URL couldn't be "
                    "auto-detected. Make sure you include "
                    "'django_extensions.urls.autocomplete' in your URLconf.")
        context = {
            'search_path': self.search_path,
            'search_fields': ','.join(self.searchable_fields),
            'model_name': model_name,
            'app_label': app_label,
            'label': label,
            'name': name,
        }
        output.append(render_to_string(self.widget_template or (
            'django_extensions/widgets/%s/%s/foreignkey_searchinput.html' % (app_label, model_name),
            'django_extensions/widgets/%s/foreignkey_searchinput.html' % app_label,
            'django_extensions/widgets/foreignkey_searchinput.html',
        ), context))
        output.reverse()
        return mark_safe(u''.join(output))
