# -*- coding: utf-8 -*-
from io import StringIO

from django.core.management import call_command


def test_show_template_tags():
    out = StringIO()
    call_command('show_template_tags', '--no-color', stdout=out)

    output = out.getvalue()

    assert "App: django.contrib.admin\n" in output
    assert "App: django_extensions\n" in output
    assert "load: highlighting\n" in output
    assert "Tag: highlight\n" in output


def test_show_template_tags_testapp():
    out = StringIO()
    call_command('show_template_tags', '--no-color', stdout=out)

    output = out.getvalue()

    assert "App: tests.testapp\n" in output
    assert "load: dummy_tags\n" in output
    assert "Tag: dummy_tag\n" in output


def test_show_template_tags_testapp_with_appconfig():
    out = StringIO()
    call_command('show_template_tags', '--no-color', stdout=out)

    output = out.getvalue()

    assert "App: tests.testapp_with_appconfig\n" in output
    assert "load: dummy_tags_appconfig\n" in output
    assert "Tag: dummy_tag_appconfig\n" in output
