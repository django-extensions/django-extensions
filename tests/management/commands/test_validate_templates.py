# -*- coding: utf-8 -*-
import pytest
from django.core.management import call_command, CommandError
from six import StringIO


def test_validate_templates():
    out = StringIO()
    try:
        call_command('validate_templates', verbosity=3, stdout=out, stderr=out)
    except CommandError:
        print(out.getvalue())
        raise

    output = out.getvalue()
    assert "0 errors found\n" in output


def test_validate_templates_with_error(settings):
    settings.INSTALLED_APPS += ['tests.testapp_with_template_errors']

    out = StringIO()
    with pytest.raises(CommandError, message="1 errors found"):
        call_command('validate_templates', verbosity=3, stdout=out, stderr=out)
