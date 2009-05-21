from django import forms
from django.conf import settings
from django.core import urlresolvers
from django.core.exceptions import ImproperlyConfigured
from django.utils.safestring import mark_safe
from django.utils.text import truncate_words
from django.template.loader import render_to_string
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django_extensions.forms.widgets import ForeignKeySearchInput

class AdminForeignKeySearchInput(ForeignKeySearchInput, ForeignKeyRawIdWidget):
    """
    A Widget for displaying ForeignKeys in an autocomplete search input 
    instead in a <select> box.
    """
    search_path = '../foreignkey_autocomplete/'

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        opts = self.rel.to._meta
        app_label = opts.app_label
        model_name = opts.object_name.lower()
        related_url = '../../../%s/%s/' % (app_label, model_name)
        params = self.url_parameters()
        if params:
            url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in params.items()])
        else:
            url = ''
        if not attrs.has_key('class'):
            attrs['class'] = 'vForeignKeyRawIdAdminField'
        # Call the TextInput render method directly to have more control
        output = [forms.TextInput.render(self, name, value, attrs)]
        if value:
            label = self.label_for_value(value)
        else:
            label = u''
        context = {
            'url': url,
            'related_url': related_url,
            'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
            'search_path': self.search_path,
            'search_fields': ','.join(self.search_fields),
            'model_name': model_name,
            'app_label': app_label,
            'label': label,
            'name': name,
        }
        output.append(render_to_string(self.widget_template or (
            'django_extensions/admin/widgets/%s/%s/foreignkey_searchinput.html' % (app_label, model_name),
            'django_extensions/admin/widgets/%s/foreignkey_searchinput.html' % app_label,
            'django_extensions/admin/widgets/foreignkey_searchinput.html',
        ), context))
        output.reverse()
        return mark_safe(u''.join(output))
