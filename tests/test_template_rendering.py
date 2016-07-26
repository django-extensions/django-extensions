# -*- coding: utf-8 -*-
from django.test import TestCase
from django.template import Context, Template


class TemplateRenderingTests(TestCase):
    def setUp(self):
        self.ctx = Context({
            'worldvar': 'world',
        })

    def test_simple_template(self):
        self.assertEqual(Template("hello world").render(self.ctx), "hello world")

    def test_simple_context(self):
        self.assertEqual(Template("hello {{ worldvar }}").render(self.ctx), "hello world")
