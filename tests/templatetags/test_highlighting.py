# -*- coding: utf-8 -*-
from django.template import Context, Template, TemplateSyntaxError
from django.test import TestCase


class HighlightTagExceptionTests(TestCase):
    """Tests for highlight tag exceptions."""

    def setUp(self):
        self.ctx = Context()

    def test_should_raise_TemplateSyntaxError(self):
        content = """{% load highlighting %}
{% highlight %}
{% endhighlight %}
"""
        with self.assertRaisesRegex(
                TemplateSyntaxError,
                "'highlight' statement requires an argument"):
            Template(content).render(self.ctx)


class HighlightTagTests(TestCase):
    """Tests for highlight tag."""

    def setUp(self):
        self.ctx = Context()

    def test_should_highlight_python_syntax_with_name(self):
        content = """{% load highlighting %}
{% highlight 'python' 'Excerpt: blah.py' %}
def need_food(self):
    print("Love is colder than death")
{% endhighlight %}"""
        expected_result = '''<div class="predesc"><span>Excerpt: blah.py</span></div><div class="highlight"><pre><span></span><span class="k">def</span> <span class="nf">need_food</span><span class="p">(</span><span class="bp">self</span><span class="p">):</span>
    <span class="nb">print</span><span class="p">(</span><span class="s2">&quot;Love is colder than death&quot;</span><span class="p">)</span>
</pre></div>'''
        result = Template(content).render(self.ctx)

        self.assertHTMLEqual(result, expected_result)

    def test_should_highlight_bash_syntax_without_name(self):
        content = """{% load highlighting %}
{% highlight 'bash' %}
echo "Hello $1"
{% endhighlight %}"""
        expected_result = '''<div class="highlight"><pre><span></span><span class="nb">echo</span> <span class="s2">&quot;Hello </span><span class="nv">$1</span><span class="s2">&quot;</span>
</pre></div>'''

        result = Template(content).render(self.ctx)

        self.assertHTMLEqual(result, expected_result)


class ParseTemplateTests(TestCase):
    """Tests for parse_teplate filter."""

    def test_should_mark_html_as_safe(self):
        ctx = Context({'value': '<h1>Hello World</h1>'})
        content = """{% load highlighting %}
{{ value|parse_template }}
"""
        expected_result = '''<h1>Hello World</h1>'''

        result = Template(content).render(ctx)

        self.assertHTMLEqual(result, expected_result)
