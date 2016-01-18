# coding=utf-8
from django_extensions.templatetags.widont import widont, widont_html


class TestTemplateTags:

    def test_widont(self):
        assert widont('Test Value') == 'Test&nbsp;Value'

    def test_widont_html(self):
        assert widont_html('<h2>Simple  example  </h2> <p>Single</p>') == '<h2>Simple&nbsp;example  </h2> <p>Single</p>'
