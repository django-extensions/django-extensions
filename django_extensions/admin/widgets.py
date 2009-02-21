from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.text import truncate_words
from django.template.loader import render_to_string
from django.contrib.admin.widgets import (ForeignKeyRawIdWidget,
                                          ManyToManyRawIdWidget)

class ForeignKeySearchInput(ForeignKeyRawIdWidget):
    """
    A Widget for displaying ForeignKeys in an autocomplete search input 
    instead in a <select> box.
    """
    # Set in subclass to render the widget with a different template
    widget_template = None
    # Set this to the patch of the search view
    search_path = '../foreignkey_autocomplete/'

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
        super(ForeignKeySearchInput, self).__init__(rel, attrs)

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
        output = [super(ForeignKeyRawIdWidget, self).render(self, name, value, attrs)]
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
            'django_extensions/widgets/%s/%s/foreignkey_searchinput.html' % (app_label, model_name),
            'django_extensions/widgets/%s/foreignkey_searchinput.html' % app_label,
            'django_extensions/widgets/foreignkey_searchinput.html',
        ), context))
        output.reverse()
        return mark_safe(u''.join(output))

class ManyToManySearchInput(ManyToManyRawIdWidget):
    """
    A Widget for displaying ManyToManys in an autocomplete search input 
    instead in a <select> box.
    """
    # Set in subclass to render the widget with a different template
    widget_template = None
    # Set this to the patch of the search view
    search_path = '../manytomany_autocomplete/'

    class Media:
        css = {
            'all': (
                'django_extensions/css/jquery.autocomplete.css',
                'django_extensions/css/jquery.autocompletefb.css'
            )
        }
        js = (
            'django_extensions/js/jquery.js',
            'django_extensions/js/jquery.bgiframe.min.js',
            'django_extensions/js/jquery.ajaxQueue.js',
            'django_extensions/js/jquery.autocomplete.js',
            'django_extensions/js/jquery.autocompletefb.js',
        )

    def __init__(self, rel, search_fields, attrs=None):
        self.search_fields = search_fields
        super(ManyToManySearchInput, self).__init__(rel, attrs)

    def label_for_label(self, label):
        obj = self.rel.to._default_manager.get(**{'pk': label})
        return obj.pk, truncate_words(obj, 14)

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
        attrs['class'] = 'vManyToManyRawIdAdminField vManyToManySearchInput'
        if value:
            labels = [self.label_for_label(v) for v in value]
            value = ','.join([str(v) for v in value])
        else:
            labels = []
            value = ''
        # Call the TextInput render method directly to have more control
        output = [forms.TextInput.render(self, name, value, attrs)]
        context = {
            'url': url,
            'related_url': related_url,
            'admin_media_prefix': settings.ADMIN_MEDIA_PREFIX,
            'search_path': self.search_path,
            'search_fields': ','.join(self.search_fields),
            'model_name': model_name,
            'app_label': app_label,
            'labels': labels,
            'name': name,
        }
        output.append(render_to_string(self.widget_template or (
            'django_extensions/widgets/%s/%s/manytomany_searchinput.html' % (app_label, model_name),
            'django_extensions/widgets/%s/manytomany_searchinput.html' % app_label,
            'django_extensions/widgets/manytomany_searchinput.html',
        ), context))
        output.reverse()
        return mark_safe(u''.join(output))
    