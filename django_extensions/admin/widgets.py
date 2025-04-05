# -*- coding: utf-8 -*-
import urllib

from django import forms
from django.contrib.admin.sites import site
from django.contrib.admin.widgets import ForeignKeyRawIdWidget
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.text import Truncator


class ForeignKeySearchInput(ForeignKeyRawIdWidget):
    """
    Widget for displaying ForeignKeys in an autocomplete search input
    instead in a <select> box.
    """

    # Set in subclass to render the widget with a different template
    widget_template = None
    # Set this to the patch of the search view
    search_path = None

    @property
    def media(self):
        js_files = [
            static("django_extensions/js/jquery.bgiframe.js"),
            static("django_extensions/js/jquery.ajaxQueue.js"),
            static("django_extensions/js/jquery.autocomplete.js"),
        ]

        return forms.Media(
            css={"all": (static("django_extensions/css/jquery.autocomplete.css"),)},
            js=js_files,
        )

    def label_for_value(self, value):
        key = self.rel.get_related_field().name
        obj = self.rel.model._default_manager.get(**{key: value})

        return Truncator(obj).words(14, truncate="...")

    def __init__(self, rel, search_fields, attrs=None):
        self.search_fields = search_fields
        super().__init__(rel, site, attrs)

    def render(self, name, value, attrs=None, renderer=None):
        if attrs is None:
            attrs = {}
        opts = self.rel.model._meta
        app_label = opts.app_label
        model_name = opts.object_name.lower()
        related_url = reverse("admin:%s_%s_changelist" % (app_label, model_name))
        if not self.search_path:
            self.search_path = urllib.parse.urljoin(
                related_url, "foreignkey_autocomplete/"
            )
        params = self.url_parameters()
        if params:
            url = "?" + "&amp;".join(["%s=%s" % (k, v) for k, v in params.items()])
        else:
            url = ""

        if "class" not in attrs:
            attrs["class"] = "vForeignKeyRawIdAdminField"
        # Call the TextInput render method directly to have more control
        output = [forms.TextInput.render(self, name, value, attrs)]

        if value:
            label = self.label_for_value(value)
        else:
            label = ""

        context = {
            "url": url,
            "related_url": related_url,
            "search_path": self.search_path,
            "search_fields": ",".join(self.search_fields),
            "app_label": app_label,
            "model_name": model_name,
            "label": label,
            "name": name,
        }
        output.append(
            render_to_string(
                self.widget_template
                or (
                    "django_extensions/widgets/%s/%s/foreignkey_searchinput.html"
                    % (app_label, model_name),
                    "django_extensions/widgets/%s/foreignkey_searchinput.html"
                    % app_label,
                    "django_extensions/widgets/foreignkey_searchinput.html",
                ),
                context,
            )
        )
        output.reverse()

        return mark_safe("".join(output))
