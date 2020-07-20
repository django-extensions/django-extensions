# -*- coding: utf-8 -*-
import os
import shutil
from html.parser import HTMLParser
from tempfile import mkdtemp

from django.template import Context, Template
from django.test import TestCase

from django_extensions.templatetags.syntax_color import generate_pygments_css


class SyntaxColorTagTests(TestCase):
    """Tests for syntax_color tags."""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = mkdtemp()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmpdir)

    def test_should_generate_pygments_css_file_in_temp_directory(self):
        generate_pygments_css(self.tmpdir)

        self.assertTrue(os.path.exists(
            os.path.join(self.tmpdir, 'pygments.css')))

    def test_pygments_css_should_return_highlight_css(self):
        content = """{% load syntax_color %}
{% pygments_css %}
"""
        result = Template(content).render(Context())

        self.assertIn('.highlight .hll', result)

    def test_should_colorize_with_default_lexer(self):
        ctx = Context({'code_string': '<h1>TEST</h1>'})
        content = """{% load syntax_color %}
{{ code_string|colorize }}
"""
        expected_result = '''<div class="highlight"><pre><span></span><span class="nt">&lt;h1&gt;</span>TEST<span class="nt">&lt;/h1&gt;</span>
</pre></div>'''
        result = Template(content).render(ctx)

        self.assertHTMLEqual(result, expected_result)

    def test_colorize_should_return_value_if_lexer_class_not_found(self):
        ctx = Context({'code_string': '<h1>TEST</h1>'})
        content = """{% load syntax_color %}
{{ code_string|colorize:'invalid_lexer' }}
"""
        expected_result = '<h1>TEST</h1>'

        result = Template(content).render(ctx)

        self.assertHTMLEqual(HTMLParser().unescape(result), expected_result)

    def test_should_colorize_table_with_default_lexer(self):
        ctx = Context({'code_string': '<h1>TEST</h1>'})
        content = """{% load syntax_color %}
{{ code_string|colorize_table }}
"""
        expected_result = '''<table class="highlighttable"><tr><td class="linenos"><div class="linenodiv"><pre>1</pre></div></td><td class="code"><div class="highlight"><pre><span></span><span class="nt">&lt;h1&gt;</span>TEST<span class="nt">&lt;/h1&gt;</span>
</pre></div>
</td></tr></table>'''

        result = Template(content).render(ctx)

        self.assertHTMLEqual(result, expected_result)

    def test_colorize_table_should_return_value_if_lexer_class_not_found(self):
        ctx = Context({'code_string': '<h1>TEST</h1>'})
        content = """{% load syntax_color %}
{{ code_string|colorize_table:'invalid_lexer' }}
"""
        expected_result = '<h1>TEST</h1>'
        result = Template(content).render(ctx)

        self.assertHTMLEqual(HTMLParser().unescape(result), expected_result)

    def test_should_colorize_noclasses_with_default_lexer(self):
        ctx = Context({'code_string': '<h1>TEST</h1>'})
        content = """{% load syntax_color %}
{{ code_string|colorize_noclasses }}
"""
        expected_result = '''<div class="highlight" style="background: #f8f8f8"><pre style="line-height: 125%"><span></span><span style="color: #008000; font-weight: bold">&lt;h1&gt;</span>TEST<span style="color: #008000; font-weight: bold">&lt;/h1&gt;</span>
</pre></div>'''
        result = Template(content).render(ctx)

        self.assertHTMLEqual(result, expected_result)

    def test_colorize_noclasses_should_return_value_if_lexer_class_not_found(self):
        ctx = Context({'code_string': '<h1>TEST</h1>'})
        content = """{% load syntax_color %}
{{ code_string|colorize_noclasses:'invalid_lexer' }}
"""
        expected_result = '<h1>TEST</h1>'
        result = Template(content).render(ctx)

        self.assertHTMLEqual(HTMLParser().unescape(result), expected_result)
