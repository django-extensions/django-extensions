# -*- coding: utf-8 -*-
from django.core.management import call_command
from django.utils.six import StringIO


def test_show_urls_format_dense():
    out = StringIO()
    call_command('show_urls', stdout=out)

    output = out.getvalue()
    assert "/admin/\tdjango.contrib.admin.sites.index\tadmin:index\n" in output
    assert "/admin/<app_label>/\tdjango.contrib.admin.sites.app_index\tadmin:app_list\n" in output


def test_show_urls_format_verbose():
    out = StringIO()
    call_command('show_urls', format="verbose", stdout=out)

    output = out.getvalue()
    assert """/login/
\tController: django.contrib.auth.views.LoginView
\tURL Name: login""" in output
