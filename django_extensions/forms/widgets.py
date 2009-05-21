from django import forms
from django.conf import settings
from django.core import urlresolvers
from django.core.exceptions import ImproperlyConfigured
from django.utils.safestring import mark_safe
from django.utils.text import truncate_words
from django.template.loader import render_to_string
from django.contrib.admin.widgets import ForeignKeyRawIdWidget

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
        js = (
            'django_extensions/js/jquery.js',
            'django_extensions/js/jquery.bgiframe.min.js',
            'django_extensions/js/jquery.ajaxQueue.js',
            'django_extensions/js/jquery.autocomplete.js',
        )

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        obj = self.rel.to._default_manager.get(**{key: value})
        return truncate_words(obj, 14)

    def __init__(self, rel, search_fields, attrs=None):
        self.search_fields = search_fields
        if self.search_path is None:
            try:
                self.search_path = urlresolvers.reverse('foreignkey_autocomplete')
            except urlresolvers.NoReverseMatch:
                raise ImproperlyConfigured(
                    "The foreignkey autocomplete URL couldn't be "
                    "auto-detected. Make sure you include "
                    "'django_extensions.urls.autocomplete' in your URLconf.")
        super(ForeignKeySearchInput, self).__init__(rel, attrs)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        opts = self.rel.to._meta
        app_label = opts.app_label
        model_name = opts.object_name.lower()
        output = [super(ForeignKeySearchInput, self).render(self, name, value, attrs)]
        if value:
            label = self.label_for_value(value)
        else:
            label = u''
        context = {
            'search_path': self.search_path,
            'search_fields': ','.join(self.search_fields),
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
