# -*- coding: utf-8 -*-
from django.apps import apps
from django.core.management.base import CommandError, LabelCommand
from django.utils.encoding import force_text

from django_extensions.management.utils import signalcommand


class Command(LabelCommand):
    help = "Outputs the specified model as a form definition to the shell."
    args = "[app.model]"
    label = 'application name and model name'

    can_import_settings = True

    @signalcommand
    def handle_label(self, label, **options):
        return describe_form(label)


def describe_form(label, fields=None):
    """
    Returns a string describing a form based on the model
    """
    try:
        app_name, model_name = label.split('.')[-2:]
    except (IndexError, ValueError):
        raise CommandError("Need application and model name in the form: appname.model")
    model = apps.get_model(app_name, model_name)

    opts = model._meta
    field_list = []
    for f in opts.fields + opts.many_to_many:
        if not f.editable:
            continue
        if fields and f.name not in fields:
            continue
        formfield = f.formfield()
        if '__dict__' not in dir(formfield):
            continue
        attrs = {}
        valid_fields = ['required', 'initial', 'max_length', 'min_length', 'max_value', 'min_value', 'max_digits', 'decimal_places', 'choices', 'help_text', 'label']
        for k, v in formfield.__dict__.items():
            if k in valid_fields and v is not None:
                # ignore defaults, to minimize verbosity
                if k == 'required' and v:
                    continue
                if k == 'help_text' and not v:
                    continue
                if k == 'widget':
                    attrs[k] = v.__class__
                elif k in ['help_text', 'label']:
                    attrs[k] = force_text(v).strip()
                else:
                    attrs[k] = v

        params = ', '.join(['%s=%r' % (k, v) for k, v in attrs.items()])
        field_list.append('    %(field_name)s = forms.%(field_type)s(%(params)s)' % {
            'field_name': f.name,
            'field_type': formfield.__class__.__name__,
            'params': params
        })
    return '''
from django import forms
from %(app_name)s.models import %(object_name)s

class %(object_name)sForm(forms.Form):
%(field_list)s
''' % {'app_name': app_name, 'object_name': opts.object_name, 'field_list': '\n'.join(field_list)}
